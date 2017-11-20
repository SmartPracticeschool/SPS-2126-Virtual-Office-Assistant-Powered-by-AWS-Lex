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
from helpers.db_helpers import validate_table
from boto3.dynamodb.conditions import Key


LOCATION_TABLE = 'PollexyLocations'


class Location(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('Name', '')


class LocationManager(object):
    def __init__(self, *kwargs):
        validate_table(LOCATION_TABLE, self.create_table)

    def convert(self, item):
        return Location(Name=item['name'])

    def create__table(self):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
                    TableName=LOCATION_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'location_name',
                            'KeyType': 'HASH'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5,
                    }
                )
        table.meta.client.get_waiter('table_exists') \
            .wait(TableName=LOCATION_TABLE)

    def get_location(self, name):
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(LOCATION_TABLE)
        response = table.query(
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression=Key('location_name').eq(name))
        if len(response['Items']) == 0:
            return None
        else:
            return self.convert_to_person(response['Items'][0])

    def get_all(self):
        dynamodb = boto3.resource('dynamodb')
        response = dynamodb.scan(
            Select='ALL_ATTRIBUTES',
            TableName=LOCATION_TABLE)

        locations = []
        if len(response['Items']) == 0:
            return None
        else:
            for i in response['Items']:
                locations.append(self.convert(i))
