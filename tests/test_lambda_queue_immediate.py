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

from mock import patch
from lambda_functions.queue_immediate import handler
from person.person import Person, PersonManager
from messages.message_manager import LibraryManager
import json
import boto3
from moto import mock_dynamodb2


def test_event():
    return json.loads("""
    {
      "session": {
        "new": true,
        "application":
            { "applicationId": "test"
        },
        "sessionId": "sessionId"
      },
      "request": {
        "requestId": "test-request",
        "type": "IntentRequest",
        "intent": {
          "name": "QueueMessage",
          "slots": {
            "person": {
              "name": "person",
              "value": "calvin"
            },
            "message": {
              "name": "message",
              "value": "dinner"
            }
          }
        }
      }
    }
    """)


@patch('lambda_functions.queue_immediate.queue_message')
def test_valid_message_calls_queue_message(qm_mock):
    handler(test_event(), {})
    assert qm_mock.called_once()


@patch('logging.Logger.error')
def test_no_person_returns_error(logerr_mock):
    e = test_event()
    del e['request']['intent']['slots']['person']
    handler(e, {})
    logerr_mock.assert_called_with('Missing person or message')


@patch('logging.Logger.error')
def test_no_message_returns_error(logerr_mock):
    e = test_event()
    del e['request']['intent']['slots']['message']
    handler(e, {})
    logerr_mock.assert_called_with('Missing person or message')


@mock_dynamodb2
@patch('person.person.PersonManager.get_person')
@patch('logging.Logger.error')
def test_invalid_person_returns_error(l_mock, p_mock):
    e = test_event()
    p_mock.return_value = None
    handler(e, {})
    l_mock.assert_called_with('calvin does not have an entry in the '
                              'Person table . . .')


@mock_dynamodb2
@patch('messages.message_manager.LibraryManager.get_message')
@patch('person.person.PersonManager.get_person')
@patch('logging.Logger.error')
def test_invalid_message_returns_error(l_mock, p_mock, m_mock):
    e = test_event()
    m_mock.return_value = None
    p_mock.return_value = Person()
    handler(e, {})
    l_mock.assert_called_with('There is no message named dinner')


@patch('logging.Logger.error')
@patch('person.person.Person.all_available_count')
@mock_dynamodb2
def test_no_locations_returns_error(c_mock, l_mock):
    e = test_event()
    client = boto3.client('dynamodb')
    client.create_table(
        AttributeDefinitions=[
            {
                'AttributeName': 'PersonName',
                'AttributeType': 'S'
            },
        ],
        TableName='PollexyPeople',
        KeySchema=[
            {
                'AttributeName': 'PersonName',
                'KeyType': 'HASH'
            }],
        ProvisionedThroughput={
            'ReadCapacityUnits': 123,
            'WriteCapacityUnits': 123
        },
    )
    lm = LibraryManager()
    lm.update_message(Name='dinner', Message='time for dinner')

    pm = PersonManager()
    p = Person(Name='calvin')
    pm.update_window_set(p)
    c_mock.return_value = 0
    handler(e, {})
    l_mock.assert_called_with('No locations are available for calvin')
