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

import boto3
import arrow
from helpers.db_helpers import validate_table
from datetime import datetime
from messages.message import ScheduledMessage  # noqa: E402
import logging

MESSAGE_SCHEDULE_DB = 'PollexyMessageSchedule'


def convert_to_scheduled_message(db_message):
    last = db_message.get("last_occurrence_in_utc", None)
    if db_message.get("last_occurrence_in_utc", None):
        last = arrow.get(last)
    return (ScheduledMessage(
        UUID=db_message["uuid"],
        StartDateTimeInUtc=arrow.get(db_message["start_datetime_in_utc"]),
        ical=db_message["ical"],
        Body=db_message["body"],
        IsQueued=db_message.get("in_queue", False),
        PersonName=db_message["person_name"],
        LastLocationIndex=db_message.get('last_location_index', 0),
        LastOccurrenceInUtc=last,
        EndDateTimeInUtc=arrow.get(db_message["end_datetime_in_utc"])))


class Scheduler(object):
    def __init__(self, *kwargs):
        logging.info('Initializing Scheduler')
        validate_table(MESSAGE_SCHEDULE_DB, self.create_schedule_table)

    def schedule_message(self, scheduled_message):
        datetime_in_utc = datetime.utcnow().isoformat()
        ical = scheduled_message.to_ical()
        body = scheduled_message.body
        person_name = scheduled_message.person_name
        end_datetime_in_utc = \
            scheduled_message.end_datetime_in_utc.isoformat()
        start_datetime_in_utc = \
            scheduled_message.start_datetime_in_utc.isoformat()

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        logging.info('Storing message in ' + MESSAGE_SCHEDULE_DB)
        table.put_item(
           Item={
               'uuid': scheduled_message.uuid_key,
               'create_time': datetime_in_utc,
               'ical': ical,
               'person_name': person_name,
               'start_datetime_in_utc': start_datetime_in_utc,
               'end_datetime_in_utc': end_datetime_in_utc,
               'body': body
            }
        )

    def get_messages(self, compare_date='', ready_only=True):
        logging.info("Checking for scheduled messages: compare_date={}," +
                     "ready_only={}".format(compare_date, ready_only))
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        response = table.scan(
              Select='ALL_ATTRIBUTES'
              )
        scheduled_messages = []
        if not compare_date:
            compare_date = arrow.utcnow()
            logging.info('Checking messages using uctnow since compare_dt ' +
                         'is empty, compare_date=%s'
                         % compare_date.isoformat())
        logging.info("Total number of scheduled messages in table %s: %s"
                     % (MESSAGE_SCHEDULE_DB, len(response['Items'])))
        for item in response['Items']:
            m = convert_to_scheduled_message(item)
            if m.no_more_occurrences:
                logging.info('Skipping message, no more occurrences')
                continue
            if not ready_only or (ready_only and
                                  m.is_message_ready(
                                      CompareDateTimeInUtc=compare_date)):
                logging.info('Adding message to response:')
                scheduled_messages.append(convert_to_scheduled_message(item))
            else:
                logging.info('Skipping message, ready_only=%s, msg_rdy=%s'
                             % (ready_only, m.is_message_ready(
                                      CompareDateTimeInUtc=compare_date)))
        logging.info("Number of scheduled messages: %s"
                     % len(scheduled_messages))
        return scheduled_messages

    def create_schedule_table(self):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
                    TableName=MESSAGE_SCHEDULE_DB,
                    KeySchema=[
                        {
                            'AttributeName': 'uuid',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'person_name',
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'uuid',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'person_name',
                            'AttributeType': 'S'
                        },
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1,
                    }
                )
        table.meta.client.get_waiter('table_exists') \
            .wait(TableName=MESSAGE_SCHEDULE_DB)

    def update_last_location(self, uuid, person_name, last_loc=0):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        table.update_item(
            Key={
                'uuid': uuid,
                'person_name': person_name
            },
            UpdateExpression='SET last_location_index=:lo',
            ExpressionAttributeValues={
                ':lo': last_loc
            }
        )

    def update_queue_status(self, uuid, person_name, is_queued=True):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        table.update_item(
            Key={
                'uuid': uuid,
                'person_name': person_name
            },
            UpdateExpression='SET in_queue=:lo',
            ExpressionAttributeValues={
                ':lo': is_queued
            }
        )

    def set_expired(self, uuid, person_name, is_expired=True):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        table.update_item(
            Key={
                'uuid': uuid,
                'person_name': person_name
            },
            UpdateExpression='SET expired=:lo',
            ExpressionAttributeValues={
                ':lo': is_expired
            }
        )

    def update_last_occurrence(self, uuid, person_name, last_occurrence=None):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        if not last_occurrence:
            last_occurrence = arrow.utcnow()
        table.update_item(
            Key={
                'uuid': uuid,
                'person_name': person_name
            },
            UpdateExpression='SET last_occurrence_in_utc=:lo',
            ExpressionAttributeValues={
                ':lo': last_occurrence.isoformat()
            }
        )

    def update_tried_locations(self, **kwargs):
        uuid = kwargs.get('UUID')
        person_name = kwargs.get('PersonName')
        location_name = kwargs.get('LocationName')
        current_locations = kwargs.get('TriedLocations')
        if not current_locations:
            current_locations = []

        current_locations.append(location_name)

        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(MESSAGE_SCHEDULE_DB)
        table.update_item(
            Key={
                'uuid': uuid,
                'person_name': person_name
            },
            UpdateExpression='SET tried_locations=:lo',
            ExpressionAttributeValues={
                ':lo': current_locations
            }
        )
