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

import arrow
import boto3
import json
from helpers.db_helpers import validate_table
from boto3.dynamodb.conditions import Key
from babylex import LexSession
from person.person import PersonManager
from time_window import TimeWindow, TimeWindowSet
import logging
import uuid
import random
from input.switch import Switch

LOCATION_TABLE = 'PollexyLocations'
HASH_KEY = 'LocationName'


def display(cal):
    return cal.to_ical().replace('\r\n', '\n').strip()


class LocationFinder(object):
    def __init__(self):
        self.locations = []

    def add_location(self, loc):
        self.locations.append(loc)


class LocationAvailability(object):
    def __init__(self, **kwargs):
        self.location_name = kwargs.get('LocationName', '')
        self.time_windows = TimeWindowSet()
        self.output_capabilities = {}
        self.input_capabilities = {}

    def add_window(self, w):
        self.time_windows.set_list.append(w)

    def add_input_capability(self, **kwargs):
        id = kwargs.get('HardwareId', str(uuid.uuid4()))
        name = kwargs.get('Name', '')
        color = kwargs.get('Color', '')
        style = kwargs.get('Style', '')
        input_type = kwargs.get('Type', '')
        self.input_capabilities[id] = {
            'name': name,
            'color': color,
            'style': style,
            'type': input_type
        }

    def with_switch(self, **kwargs):
        kwargs['Type'] = 'switch'
        self.add_input_capability(**kwargs)

    def is_available(self, dt=None):
        if not dt:
            dt = arrow.utcnow()
        return self.time_windows.is_available(dt=dt)


class LocationStatus(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('Name')
        self.last_heartbeat_dt = kwargs.get('LastHeartbeat')
        self.last_movement = kwargs.get('LastMovement')


class LocationManager(object):
    def __init__(self, **kwargs):
        validate_table(LOCATION_TABLE, self.create_location_table)

    def create_location_table(self):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
                    TableName=LOCATION_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': HASH_KEY,
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': HASH_KEY,
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5,
                    }
                )
        table.meta.client.get_waiter('table_exists') \
            .wait(TableName=LOCATION_TABLE)

    def upsert(self, **kwargs):
        name = kwargs.get('Name')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        table.update_item(
            Key={
                HASH_KEY: name
            },
            UpdateExpression='SET CreateDate=:lo',
            ExpressionAttributeValues={
                ':lo': arrow.utcnow().isoformat()
            }
        )

    def delete(self, **kwargs):
        name = kwargs.get('Name')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        table.delete_item(
            Key={
                HASH_KEY: name
            }
        )

    def update_location_activity(self, loc_name):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        table.update_item(
            Key={
                HASH_KEY: loc_name
            },
            UpdateExpression='SET last_activity=:lo',
            ExpressionAttributeValues={
                ':lo': arrow.utcnow().isoformat()
            }
        )

    def toggle_mute(self, loc_name, is_muted=False):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        table.update_item(
            Key={
                HASH_KEY: loc_name
            },
            UpdateExpression='SET is_muted=:lo',
            ExpressionAttributeValues={
                ':lo': is_muted
            }
        )

    def update_input_capabilities(self, loc_avail):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        table.update_item(
            Key={
                HASH_KEY: loc_avail.location_name
            },
            UpdateExpression='SET input_capabilities=:ic',
            ExpressionAttributeValues={
               ':ic': json.dumps(loc_avail.input_capabilities)
            }
        )

    def update_window_set(self, loc_avail):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        table.update_item(
            Key={
                HASH_KEY: loc_avail.location_name
            },
            UpdateExpression='SET windows=:ws',
            ExpressionAttributeValues={
                ':ws': loc_avail.time_windows.to_json(),
            }
        )

    def convert_to_loc_avail(self, db_loc):
        la = LocationAvailability()
        la.location_name = db_loc[HASH_KEY]
        if 'is_muted' in list(db_loc.keys()):
            la.is_muted = db_loc['is_muted']

        if 'windows' in list(db_loc.keys()):
            for w in json.loads(db_loc['windows']):
                tw = TimeWindow(IsMuted=w["is_muted"],
                                ical=w['ical'],
                                Priority=w['priority'])

                la.add_window(tw)
        if 'last_activity' in list(db_loc.keys()):
            la.last_activity = arrow.get(db_loc['last_activity'])
            logging.info('Last motion was ' + la.last_activity.isoformat())
            if ((arrow.utcnow()-la.last_activity).seconds > 60):
                la.is_motion = False
            else:
                la.is_motion = True

        if 'input_capabilities' in list(db_loc.keys()):
            for k in json.loads(db_loc['input_capabilities']):
                i = json.loads(db_loc['input_capabilities'])[k]
                la.add_input_capability(
                    HardwareId=k,
                    Name=i['name'],
                    Color=i['color'],
                    Style=i['style'],
                    Type=i['type'])

        return la

    def get_location(self, loc_name):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        response = table.query(
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression=Key(HASH_KEY).eq(loc_name))
        if len(response['Items']) == 0:
            return None
        else:
            return self.convert_to_loc_avail(response['Items'][0])

    def get_all(self):
        dynamodb = boto3.client('dynamodb')
        response = dynamodb.scan(
            Select='ALL_ATTRIBUTES',
            TableName=LOCATION_TABLE)

        locs = []
        if len(response['Items']) == 0:
            return None
        else:
            for i in response['Items']:
                locs.append(self.convert_to_loc_avail(i))
            return locs


class LocationVerification(object):
    def __init__(self, **kwargs):
        self.location_name = kwargs.get('LocationName', '')
        self.person_name = kwargs.get('PersonName', '')
        self.voice = kwargs.get('VoiceId', 'Joanna')

        self.lex = LexSession(bot="PlexyMessenger", alias="$LATEST",
                              user=self.location_name)
        self.person = PersonManager().get_person(self.person_name)
        self.location = LocationManager().get_location(self.location_name)
        self.timeout_in_secs = kwargs.get('TimeoutInSeconds', 15)
        self.retry_count = kwargs.get('RetryCount', 4)

    # TODO: add motion sensing, allow multiple input types
    #       this is very hard-coded to switches
    def verify_person_at_location(self, **kwargs):
        if not self.person.require_physical_confirmation or \
                not hasattr(self.location, 'input_capabilities'):
            return True, 0, 0

        if len(list(self.location.input_capabilities.keys())) > 0:
            id = kwargs.get('HardwareId')
            speech_method = kwargs.get('SpeechMethod')

            if id:
                s_id = id

            else:
                s_id = random.choice(list(self.location.input_capabilities.keys()))

            s = Switch(HardwareId=s_id,
                       TimeoutInSeconds=self.timeout_in_secs)

            c = 0
            done = False
            while c < self.retry_count and not done:
                c = c + 1
                i_name = self.location.input_capabilities[s_id]['name']
                speech_method(Message='Please push the {}'.format(i_name),
                              IncludeChime=True,
                              VoiceId=self.voice)
                done, timeout = s.wait_for_input()

            return done, c, timeout

    def verify_valid_user(self):
        lex_session = LexSession(bot="PlexyMessenger", alias="$LATEST",
                                 user="troy")
        resp = lex_session.text('Verify location for ' + self.person_name)
        if 'message' in resp and 'No usable messages' in str(resp['message']):
            raise ValueError('Person does not exist in the db:'
                             + self.person_name)

        if 'dialogState' in resp and \
           resp['dialogState'] == 'ReadyForFulfillment':
            return True

        return False

    def send_confirm_response(self, **kwargs):
        if 'AudioContent' in kwargs:
            data = kwargs.get('AudioContent')
            resp = self.lex.content(data)

        if 'TextResponse' in kwargs:
            text_resp = kwargs.get('TextResponse')
            resp = self.lex.text(text_resp)

        if 'x-amz-lex-message' in resp:
            if 'confirmed' in resp['x-amz-lex-message']:
                return 'Confirmed'

            if 'Sorry, I could not understand.' in resp['x-amz-lex-message']:
                return 'NotUnderstood'
