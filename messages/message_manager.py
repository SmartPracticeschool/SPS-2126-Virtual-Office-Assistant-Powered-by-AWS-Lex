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
from message import QueuedMessage
from scheduler.scheduler import Scheduler
import logging
from person.person import PersonManager
from helpers.speech import SpeechHelper
from helpers.db_helpers import validate_table
import uuid
import os

MESSAGE_LIBRARY_TABLE = 'PollexyMessageLibrary'


def get_queue(location_name):
    """get a queue by name"""
    log = logging.getLogger("GetQueue")
    if os.environ.get('LOG_LEVEL') == 'DEBUG':
        log.setLevel(logging.DEBUG)
    sqs = boto3.resource('sqs')
    client = boto3.client('sqs')
    queue_name = 'pollexy-inbox-%s' % (location_name)
    queue_url = ""
    try:
        log.debug('Getting queue: {}'.format(queue_name))
        queue_url = client.get_queue_url(QueueName=queue_name)

    except Exception as e:
        log.error('Error getting queue: {}'.format(e))
        return None

    for queue in sqs.queues.all():
        if queue.url == queue_url['QueueUrl']:
            log.debug('Queue already exists')
            return queue


class MessageManager(object):
    """interacts with the message queue"""
    def __init__(self, **kwargs):
        self.log = logging.getLogger("MessageManager")
        if os.environ.get('LOG_LEVEL') == 'DEBUG':
            self.log.setLevel(logging.DEBUG)
        self.location_name = kwargs.get("LocationName", "").lower()
        if len(self.location_name) == 0:
            raise ValueError('Missing location name')

        self.queue_name = "pollexy-inbox-%s" % (self.location_name)
        self.bot_queue_name = "{}-bot".format(self.queue_name)
        self.log.debug('Initializing queue manager, Queue name: {}'
                       .format(self.queue_name))
        self.validate_queue()
        self.messages = {}

    def validate_queue(self):
        """validate the queue and create if it doesn't exist"""
        sqs = boto3.resource('sqs')
        queue = None
        bot_queue = None
        self.log.debug('Validating queue')
        try:
            bot_queue = get_queue('{}-bot'.format(self.location_name))
            if bot_queue is None:
                self.log.debug('Bot queue does not exist, creating . . .')
                bot_queue = sqs.create_queue(QueueName=self.bot_queue_name)
            queue = get_queue(self.location_name)
            if queue is None:
                self.log.debug('Message queue does not exist, creating . . .')
                queue = sqs.create_queue(QueueName=self.bot_queue_name)
        except Exception as e:
            self.log.error(e)
            self.is_valid_queue = False
            raise
        else:
            self.log.debug('Queue validated: {}'.format(self.bot_queue_name))
            self.log.debug('Queue validated: {}'.format(self.queue_name))
            self.is_valid_queue = True
            self.queue = queue
            self.bot_queue = bot_queue

    def get_messages(self, **kwargs):
        person_name = kwargs.get('PersonName', '')
        message_type = kwargs.get('MessageType', 'Message')
        self.sqs_msgs = []
        self.log.debug("Checking messages in the queue, person={}, type={}"
                       .format(person_name, message_type))
        messages = {}
        queue = None
        if message_type == "Message":
            queue = self.queue
        else:
            queue = self.bot_queue
        messages = queue.receive_messages(
            MessageAttributeNames=['NoMoreOccurrences',
                                   'ExpirationDateTimeInUtc',
                                   'PersonName',
                                   'Voice',
                                   'BotNames',
                                   'RequiredBots',
                                   'IceBreaker',
                                   'UUID'],
            WaitTimeSeconds=20,
            MaxNumberOfMessages=10)
        self.log.debug(len(messages))
        if len(messages) > 0:
            self.log.debug('Received {}:'.format(len(messages)))
            msgs = []
            for m in messages:
                qm = QueuedMessage(QueuedMessage=m)
                if not qm.person_name == person_name:
                    self.log.debug('Skipping message for {}, looking for {}'
                                   .format(qm.person_name, person_name))
                    continue
                if qm.person_name not in self.messages:
                    self.log.debug("First message for " + qm.person_name)
                    self.messages[qm.person_name] = []
                self.messages[qm.person_name].append(qm)
                self.sqs_msgs.append(m)
                msgs.append(qm)
                scheduler = Scheduler()
                scheduler.update_queue_status(qm.uuid_key,
                                              person_name,
                                              False)
                return msgs

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

    def fail_messages(self, **kwargs):
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

    def succeed_messages(self, **kwargs):
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
        expiration_date = kwargs.pop('ExpirationDateTimeInUtc',
                                     '2299-12-31 00:00:00')
        body = kwargs.pop('Body', '')
        uuid_key = kwargs.pop('UUID', str(uuid.uuid4()))
        no_more_occ = kwargs.pop('NoMoreOccurrences', False)
        person_name = kwargs.pop('PersonName', '')
        bot_names = kwargs.pop('BotNames', '')
        required_bots = kwargs.pop('RequiredBots', '')
        ice_breaker = kwargs.pop('IceBreaker', '')
        voice = kwargs.pop('VoiceId', 'Joanna')
        if not person_name:
            raise ValueError("No person provided")
        if not uuid_key:
            raise ValueError("No uuid provided")
        if not body:
            raise ValueError('No message body provided')
        if kwargs:
            raise TypeError('Unexpected **kwargs: %r' % kwargs)
        self.log.debug('Publishing message to {}:\n{}'
                       .format(self.queue_name, body))

        pm = PersonManager()
        p = pm.get_person(person_name)
        windows = p.time_windows.to_json()
        msg_attr = {
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
            }}

        if required_bots:
            msg_attr['RequiredBots'] = {
                'StringValue': required_bots,
                'DataType': 'String'
            }

        if bot_names:
            msg_attr['BotNames'] = {
                'StringValue': bot_names,
                'DataType': 'String'
            }

        if ice_breaker:
            msg_attr['IceBreaker'] = {
                'StringValue': ice_breaker,
                'DataType': 'String'
            }
        if bot_names:
            self.log.debug('Publishing to bot queue')
            self.bot_queue.send_message(MessageBody=body,
                                        MessageAttributes=msg_attr)
        else:
            self.log.debug('Publishing to message queue')
            self.queue.send_message(MessageBody=body,
                                    MessageAttributes=msg_attr)


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
