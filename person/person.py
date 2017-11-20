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
import json
import arrow
import yaml
from time_window import TimeWindowSet, TimeWindow
from boto3.dynamodb.conditions import Key


PERSON_TABLE = 'PollexyPeople'
PERSON_HASH_KEY = 'PersonName'


class PersonTimeWindow(TimeWindow):
    def __init__(self, *args, **kwargs):
        super(PersonTimeWindow, self).__init__(*args, **kwargs)
        self.location_name = kwargs.get('LocationName', '')

    def to_json(self):
        return {'location_name': self.location_name,
                'ical': self.ical,
                'is_muted': self.is_muted,
                'priority': self.priority
                }


class Person(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('Name', '')
        self.time_windows = TimeWindowSet()
        self.require_physical_confirmation = False

    def add_windows(self, windows):
        for w in windows:
            ptw = PersonTimeWindow(LocationName=w['LocationName'],
                                   ical=w['ICal'],
                                   Priority=w['Priority'],
                                   IsMuted=w['IsMuted'])
            print 'adding window'
            self.add_window(ptw)

    def add_window(self, w):
        self.time_windows.set_list.append(w)

    def all_available(self, dt=None):
        if not dt:
            dt = arrow.utcnow()
        return sorted(self.time_windows.all_available(dt=dt),
                      key=lambda a: a.priority,
                      reverse=True)

    def all_available_count(self, dt=None):
        return sum(1 for _ in self.all_available(dt))

    def remove_window_location(self, ln):
        self.time_windows.set_list = \
            filter(lambda w: w.location_name != ln, self.time_windows.set_list)


class PersonManager(object):
    def __init__(self, *kwargs):
        pass

    def toggle_mute(self, person_name, is_muted=False):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(PERSON_TABLE)
        table.update_item(
            Key={
                PERSON_HASH_KEY: person_name
            },
            UpdateExpression='SET is_muted=:lo',
            ExpressionAttributeValues={
                ':lo': is_muted
            }
        )

    def update_window_set(self, person):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(PERSON_TABLE)
        table.update_item(
            Key={
                PERSON_HASH_KEY: person.name
            },
            UpdateExpression='SET windows=:ws, req_phys_confirm=:pc',
            ExpressionAttributeValues={
                ':ws': person.time_windows.to_json(),
                ':pc': person.require_physical_confirmation
            }
        )

    def convert_to_person(self, db_person):
        p = Person(Name=db_person[PERSON_HASH_KEY])
        if 'req_phys_confirm' in db_person.keys():
            p.require_physical_confirmation = \
                bool(db_person['req_phys_confirm'])
        else:
            p.require_physical_confirmation = False

        if 'is_muted' in db_person.keys():
            p.is_muted = db_person['is_muted']

        if 'windows' in db_person.keys():
            print db_person['windows']
            for w in json.loads(db_person['windows']):
                tw = PersonTimeWindow(IsMuted=w["is_muted"],
                                      ical=w['ical'],
                                      LocationName=w['location_name'],
                                      Priority=w['priority'])

                p.add_window(tw)

        return p

    def update_person(self, **kwargs):
        dynamodb = boto3.resource('dynamodb')
        name = kwargs.get('Name')
        windows = kwargs.get('Windows')
        req_phys_conf = kwargs.get('RequirePhysicalConfirmation')
        attr = {}
        expr = []
        upd_expr = ""
        if windows:
            expr.append('windows=:windows')
            print json.dumps(windows)
            attr[':windows'] = json.dumps(yaml.load(windows))

        if req_phys_conf is not None:
            expr.append('req_phys_confirm=:pc')
            attr[':pc'] = req_phys_conf

        if len(expr) > 0:
            upd_expr = 'SET ' + ",".join(expr)

        table = dynamodb.Table(PERSON_TABLE)
        if (upd_expr):
            table.update_item(
                Key={
                    PERSON_HASH_KEY: name
                },
                UpdateExpression=upd_expr,
                ExpressionAttributeValues=attr
            )
        else:
            table.update_item(
                Key={
                    PERSON_HASH_KEY: name
                }
            )

    def get_all(self, **kwargs):
        dynamodb_cl = boto3.client('dynamodb')
        resp = dynamodb_cl.scan(
            Select='ALL_ATTRIBUTES',
            TableName=PERSON_TABLE,
        )
        people = []
        if len(resp['Items']) == 0:
            return None
        else:
            for p in resp['Items']:
                person = {}
                if 'windows' in p.keys():
                    person['windows'] = p['windows']['S']
                if 'req_phys_confirm' in p.keys():
                    person['req_phys_confirm'] = p['req_phys_confirm']['BOOL']
                person['PersonName'] = p['PersonName']['S']
                people.append(self.convert_to_person(person))

        return people

    def get_person(self, name):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(PERSON_TABLE)
        response = table.query(
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression=Key(PERSON_HASH_KEY).eq(name))
        if len(response['Items']) == 0:
            return None
        else:
            return self.convert_to_person(response['Items'][0])
