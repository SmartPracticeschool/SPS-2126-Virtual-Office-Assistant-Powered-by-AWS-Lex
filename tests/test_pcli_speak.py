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
from cli.pollexy import cli
from mock import patch
from moto import mock_sqs, mock_dynamodb2
from messages.message_manager import MessageManager
from scheduler.scheduler import Scheduler


class Config():
    def __init__(self):
        self.value = 777


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_speak_missing_device_name_throws_error(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['speak'])
    assert not result.exit_code == 0 and \
        'Missing --device_name' in result.output


@mock_sqs
@mock_dynamodb2
@patch('messages.message.ScheduledMessage')
def test_passing_speak_calls_speak_method(mock_msg):
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['--device_name', 'test', 'speak'])
    assert 'Checking for messages . . .' in result.output


@mock_sqs
@mock_dynamodb2
def test_passing_simulate_flag_enables_simulation_mode():
    runner = CliRunner()
    result = runner.invoke(cli, obj=Config(),
                           args=['--simulate',
                                 '--device_name', 'test', 'speak'])
    assert '*SIMULATION ONLY*' in result.output


@mock_sqs
@mock_dynamodb2
def test_passing_simulate_flag_does_not_publish():
    with patch.object(MessageManager, 'publish_message') as publish_mock:
        runner = CliRunner()
        runner.invoke(cli, obj=Config(),
                      args=['--simulate', '--device_name', 'test', 'queue'])
    assert publish_mock.call_count == 0


