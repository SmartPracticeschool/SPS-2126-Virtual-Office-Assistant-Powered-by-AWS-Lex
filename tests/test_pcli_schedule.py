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

from click.testing import CliRunner
from pcli import cli
from mock import patch
from moto import mock_sqs, mock_dynamodb2


class Config():
    def __init__(self):
        self.value = 777


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_setting_expiration_and_days_after_throws_error(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['--message', 'Hey', '--device_name',
                                 'test', '--start_datetime',
                                 '2012-01-01 12:00',
                                 '--expire_after_days', '1',
                                 '--expiration_datetime',
                                 '2012-03-01 12:00', 'schedule'])
    assert not result.exit_code == 0 and \
        "Can't pass these items at the same time: " \
        "expire_after_days, expiration_datetime"


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_custom_start_time_sets_custom_time(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['--message', 'Hey', '--person_name',
                                 'test', '--start_datetime',
                                 '2012-01-01 12:00', 'schedule'])
    assert result.exit_code == 0 and \
        'Setting custom start time to' in result.output


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_no_start_time_sets_to_now(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['--message', 'Hey', '--person_name',
                                 'test', 'schedule'])
    assert result.exit_code == 0 and \
        'Setting start time to now' in result.output


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_schedule_missing_message_throws_error(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['schedule'])
    assert not result.exit_code == 0 and \
        'Missing --message' in result.output


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_schedule_missing_person_name_throws_error(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['--message', 'test', 'schedule'])
    assert not result.exit_code == 0 and \
        'Missing --person_name' in result.output
