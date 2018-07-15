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
from messages.message import ScheduledMessage
from scheduler.scheduler import Scheduler
from person.person import Person, PersonManager, PersonTimeWindow
from tests.test_person import ical_event
import arrow
import logging
import traceback


class Config():
    def __init__(self):
        self.value = 777


mock_message1 = ScheduledMessage(
    StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
    ical="FREQ=DAILY",
    Body="Test Message Body",
    PersonName="calvin",
    EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))


def chloe_three_rooms(now_dt):
    p = Person(Name='chloe')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='dining_room', Priority=300,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='media_room', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    pm = PersonManager()
    pm.update_window_set(p)


def calvin_three_rooms(now_dt):
    p = Person(Name='calvin')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='media_room', Priority=300,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    pm = PersonManager()
    pm.update_window_set(p)


@mock_sqs
@mock_dynamodb2
def test_passing_simulate_flag_simulates_publish():
    with patch.object(Scheduler, 'get_messages',
                      return_value=[mock_message1]):
        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--simulate', "--location_name", "test",
                                     'queue'])
    assert 'Publishing message(simulated):' in result.output


@mock_sqs
@mock_dynamodb2
def test_passing_simulate_flag_does_not_publish():
    with patch.object(MessageManager, 'publish_message') as publish_mock:
        runner = CliRunner()
        runner.invoke(cli, obj=Config(),
                      args=['--simulate',
                            '--location_name', 'test'
                            'queue'])
    assert publish_mock.call_count == 0


@mock_sqs
@mock_dynamodb2
@patch('scheduler.scheduler.Scheduler.get_messages')
def test_no_simulate_flag_calls_publish(get_msgs_mock):
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    calvin_three_rooms(now_dt)
    get_msgs_mock.return_value = [mock_message1]
    with patch.object(MessageManager, 'publish_message') as publish_mock:
        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--simulate_dt', now_dt.isoformat(),
                                     'queue'])
    # if result.exit_code > 0:
    exc_type, exc_value, exc_traceback = result.exc_info
    logging.error(traceback.format_exception(exc_type,
                  exc_value, exc_traceback))
    assert publish_mock.call_count == 1


@mock_sqs
@mock_dynamodb2
@patch('scheduler.scheduler.Scheduler.get_messages')
def test_multiple_messages_publishes_multiple(get_msgs_mock):
    now_dt = arrow.get('2014-01-01T10:09:00.000-05:00')
    calvin_three_rooms(now_dt)
    get_msgs_mock.return_value = [mock_message1, mock_message1]
    with patch.object(MessageManager, 'publish_message') as publish_mock:
        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--location_name', 'kitchen',
                                     '--simulate_dt', now_dt.isoformat(),
                                     '--person_name', 'calvin',
                                     'queue'])
    # if result.exit_code > 0:
    exc_type, exc_value, exc_traceback = result.exc_info
    logging.error(traceback.format_exception(exc_type,
                  exc_value, exc_traceback))
    assert publish_mock.call_count == 2


@mock_sqs
@mock_dynamodb2
def test_person_location_priority_is_used_to_queue():
    p = Person(Name='calvin')
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    pm = PersonManager()
    pm.update_window_set(p)
    with patch.object(Scheduler, 'get_messages',
                      return_value=[mock_message1]):
        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--location_name', 'test',
                                     '--simulate_dt', now_dt.isoformat(),
                                     'queue'])
    if result.exit_code > 0:
        exc_type, exc_value, exc_traceback = result.exc_info
        logging.error(traceback.format_exception(exc_type,
                      exc_value, exc_traceback))
    assert 'Publishing message for person calvin to location bedroom' in \
           result.output


@mock_sqs
@mock_dynamodb2
def test_person_location_out_of_order_priorities_are_correct():
    p = Person(Name='calvin')
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='media_room', Priority=300,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    pm = PersonManager()
    pm.update_window_set(p)
    with patch.object(Scheduler, 'get_messages',
                      return_value=[mock_message1]):
        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--location_name', 'test',
                                     '--simulate_dt', now_dt.isoformat(),
                                     'queue'])
    if result.exit_code > 0:
        exc_type, exc_value, exc_traceback = result.exc_info
        logging.error(traceback.format_exception(exc_type,
                      exc_value, exc_traceback))
    assert 'Publishing message for person calvin to location media_room' in \
           result.output


@mock_sqs
@mock_dynamodb2
def test_person_location_out_of_window_does_not_queue_anything():
    now_dt = arrow.get('2014-01-01T06:09:00.000-05:00')
    calvin_three_rooms(now_dt)
    with patch.object(Scheduler, 'get_messages',
                      return_value=[mock_message1]):

        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--location_name', 'test',
                                     '--simulate_dt', now_dt.isoformat(),
                                     'queue'])
    if result.exit_code > 0:
        exc_type, exc_value, exc_traceback = result.exc_info
        logging.error(traceback.format_exception(exc_type,
                      exc_value, exc_traceback))
    assert 'No locations available for calvin' in result.output


@mock_sqs
@mock_dynamodb2
def two_test_persons_publish_two_messages():
    now_dt = arrow.get('2014-01-01T06:09:00.000-05:00')
    chloe_three_rooms(now_dt)
    calvin_three_rooms(now_dt)
    with patch.object(Scheduler, 'get_messages',
                      return_value=[mock_message1]):

        runner = CliRunner()
        result = runner.invoke(cli, obj=Config(),
                               args=['--location_name', 'test',
                                     '--simulate_dt', now_dt.isoformat(),
                                     'queue'])
    if result.exit_code > 0:
        exc_type, exc_value, exc_traceback = result.exc_info
        logging.error(traceback.format_exception(exc_type,
                      exc_value, exc_traceback))
    assert 'Publishing message for person calvin to location media_room' in \
           result.output
    assert 'Publishing message for person chloe to location dining_room' in \
           result.output
