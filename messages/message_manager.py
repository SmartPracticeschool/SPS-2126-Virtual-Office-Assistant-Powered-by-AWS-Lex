# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not
# use this file except in compliance with the License. A copy of the
# License is located at:
#    http://aws.amazon.com/asl/
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, expressi
# or implied. See the License for the specific language governing permissions
# and limitations under the License.

"""interacts with the message queue, reading and publishing messages"""
import boto3
import botocore
from message import QueuedMessage
from scheduler.scheduler import Scheduler
import logging
from person.person import PersonManager
from helpers.speech import SpeechHelper
from helpers.db_helpers import validate_table
import uuid

MESSAGE_LIBRARY_TABLE = 'PollexyMessageLibrary'


def get_queue(location_name):
    """get a queue by name"""
    sqs = boto3.resource('sqs')
    client = boto3.client('sqs')
    queue_name = 'pollexy-inbox-%s' % (location_name)
    queue_url = ""
    try:
        queue_url = client.get_queue_url(QueueName=queue_name)

    except botocore.exceptions.ClientError as exception:
        if 'NonExistentQueue' in exception:
            return None

    except Exception as e:
        print e
        raise

    for queue in sqs.queues.all():
        if queue.url == queue_url:
            return queue


class MessageManager(object):
    """interacts with the message queue"""
    def __init__(self, **kwargs):
        self.location_name = kwargs.get("LocationName", "").lower()
        if len(self.location_name) == 0:
            raise ValueError('Missing location name')

        self.queue_name = "pollexy-inbox-%s" % (self.location_name)
        print "Connecting to queue . . . "
        self.validate_queue()
        print "Connected."
        self.messages = {}

    def validate_queue(self):
        """validate the queue and create if it doesn't exist"""
        sqs = boto3.resource('sqs')
        queue = None
        try:
            queue = get_queue(self.location_name)
            if queue is None:
                queue = sqs.create_queue(QueueName=self.queue_name)
        except Exception as e:
            print e
            self.is_valid_queue = False
            raise
        else:
            self.is_valid_queue = True
            self.queue = queue

    def get_messages(self, **kwargs):
        person_name = kwargs.get('PersonName', '')
        self.sqs_msgs = []
        """get all available messages off the queue"""
        print "Checking message queue"
        messages = self.queue.receive_messages(
            MessageAttributeNames=['NoMoreOccurrences',
                                   'ExpirationDateTimeInUtc',
                                   'PersonName',
                                   'Voice',
                                   'UUID'],
            WaitTimeSeconds=20,
            MaxNumberOfMessages=10)
        if len(messages) > 0:
            for m in messages:
                qm = QueuedMessage(QueuedMessage=m)
                if not qm.person_name == person_name:
                    continue
                if qm.person_name not in self.messages:
                    logging.info("First message for " + qm.person_name)
                    self.messages[qm.person_name] = []
                logging.info('Adding message:\n')
                logging.info(qm.body)
                self.messages[qm.person_name].append(qm)
                logging.info('Total messages so far: ' +
                             str(len(self.messages[qm.person_name])))
                self.sqs_msgs.append(m)
                scheduler = Scheduler()
                scheduler.update_queue_status(qm.uuid_key,
                                              person_name,
                                              False)

    def write_speech(self, **kwargs):
        dont_delete = kwargs.get('DontDelete', False)
        person_name = kwargs.get('PersonName', '')
        print 'getting messages for ' + person_name
        self.get_messages(DontDelete=dont_delete, PersonName=person_name)
        if len(self.messages) == 0:
            return None, None
        speech = "<speak>"
        for m in self.messages[person_name]:
            if not m.is_expired:
                speech = speech + "<p>%s</p>" % m.body
        if speech == "<speak>":
            return None, None
        speech = "%s</speak>" % speech
        sh = SpeechHelper(PersonName=person_name)
        return m.voice_id, sh.replace_tokens(speech)

    def delete_sqs_msgs(self):
        for m in self.sqs_msgs:
            logging.info('Deleting message from queue')
            m.delete()

    def fail_speech(self, **kwargs):
        logging.info('Speech failed: ' + kwargs.get('Reason',
                                                    'Unknown Reason'))
        dont_delete = kwargs.get('DontDelete', False)
        if (dont_delete):
            logging.info('We are NOT deleting the original SQS messages')
            return
        for m in self.sqs_msgs:
            scheduler = Scheduler()
            qm = QueuedMessage(QueuedMessage=m)
            logging.info("Setting messages InQueue to False")
            scheduler.update_queue_status(qm.uuid_key, qm.person_name, False)
        self.delete_sqs_msgs()

    def succeed_speech(self, **kwargs):
        logging.info('Speech succeeded.')
        dont_delete = kwargs.get('DontDelete', False)
        if (dont_delete):
            logging.info('We are NOT deleting the original SQS messages')
            return

        scheduler = Scheduler()
        for m in self.sqs_msgs:
            logging.info('Deleting message from queue')
            qm = QueuedMessage(QueuedMessage=m)
            scheduler.update_last_occurrence(qm.uuid_key, qm.person_name)
            scheduler.update_queue_status(qm.uuid_key, qm.person_name, False)
            print('No more occurrences = {}'.format(qm.no_more_occurrences))
            if qm.no_more_occurrences:
                scheduler.set_expired(qm.uuid_key, qm.person_name)
        self.delete_sqs_msgs()

    def publish_message(self, **kwargs):
        """publish a single message to the queue"""
        expiration_date = kwargs.pop('ExpirationDateTimeInUtc',
                                     '2299-12-31 00:00:00')
        body = kwargs.pop('Body', '')
        uuid_key = kwargs.pop('UUID', str(uuid.uuid4()))
        no_more_occ = kwargs.pop('NoMoreOccurrences', False)
        person_name = kwargs.pop('PersonName', '')
        voice = kwargs.pop('VoiceId', 'Joanna')
        if not person_name:
            raise ValueError("No person provided")
        if not uuid_key:
            raise ValueError("No uuid provided")
        if not body:
            raise ValueError('No message body provided')
        if kwargs:
            raise TypeError('Unexpected **kwargs: %r' % kwargs)
        logging.info("************************")

        pm = PersonManager()
        p = pm.get_person(person_name)
        windows = p.time_windows.to_json()
        self.queue.send_message(MessageBody=body,
                                MessageAttributes={
                                    'PersonName': {
                                        'StringValue': person_name,
                                        'DataType': 'String'
                                    },
                                    'Locations': {
                                        'StringValue': windows,
                                        'DataType': 'String'
                                    },
                                    'ExpirationDateTimeInUtc': {
                                        'StringValue': expiration_date,
                                        'DataType': 'String'
                                    },
                                    'UUID': {
                                        'StringValue': uuid_key,
                                        'DataType': 'String'
                                    },
                                    'NoMoreOccurrences': {
                                        'StringValue': str(no_more_occ),
                                        'DataType': 'String'
                                    },
                                    'Voice': {
                                        'StringValue': voice,
                                        'DataType': 'String'
                                    }
                                })


class LibraryManager(object):
    def __init__(self):
        validate_table(MESSAGE_LIBRARY_TABLE,
                       self.create_message_library_table)

    def create_message_library_table(self):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
                    TableName=MESSAGE_LIBRARY_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'name',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'name',
                            'AttributeType': 'S'
                        },
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1,
                    }
                )
        table.meta.client.get_waiter('table_exists') \
            .wait(TableName=MESSAGE_LIBRARY_TABLE)

    def update_message(self, **kwargs):
        name = kwargs.get('Name')
        message = kwargs.get('Message')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_LIBRARY_TABLE)
        table.put_item(
           Item={
               'name': name,
               'message': message
            }
        )

    def get_message(self, **kwargs):
        name = kwargs.get('Name')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_LIBRARY_TABLE)
        resp = table.get_item(
                Key={
                    'name': name
                }
            )

        if 'Item' not in resp.keys():
            return None

        print resp['Item']
        return(resp['Item'])

    def delete_message(self, **kwargs):
        name = kwargs.get('Name')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_LIBRARY_TABLE)
        table.delete_item(
            Key={
                'name': name
            }
        )
