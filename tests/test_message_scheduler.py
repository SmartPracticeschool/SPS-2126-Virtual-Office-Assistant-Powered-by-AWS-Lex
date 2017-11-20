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

from moto import mock_dynamodb2
import datetime
import pytest
import arrow
from scheduler.scheduler import Scheduler, MESSAGE_SCHEDULE_DB
from messages.message import ScheduledMessage
from helpers.db_helpers import does_table_exist


@pytest.fixture
def good_scheduled_message():
    return ScheduledMessage(
        StartDateTimeInUtc=arrow.utcnow().replace(days=-7),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.utcnow().replace(days=5))


@mock_dynamodb2
def test_create_table_if_missing():
    Scheduler()
    assert does_table_exist(MESSAGE_SCHEDULE_DB)


@mock_dynamodb2
def test_inserting_schedule_set_sender(good_scheduled_message):
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(good_scheduled_message)
    messages = scheduler_under_test.get_messages()
    print messages
    assert len(messages) == 1


@mock_dynamodb2
def test_inserting_schedule_sets_start_datetime(good_scheduled_message):
    start_datetime_in_utc = good_scheduled_message.start_datetime_in_utc
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(good_scheduled_message)
    message = scheduler_under_test.get_messages()[0]
    start_date = message.start_datetime_in_utc
    assert start_date.isoformat() == start_datetime_in_utc.isoformat()


@mock_dynamodb2
def test_inserting_schedule_sets_end_datetime(good_scheduled_message):
    end_datetime_in_utc = good_scheduled_message.end_datetime_in_utc
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(good_scheduled_message)
    message = scheduler_under_test.get_messages()[0]
    end_datetime = message.end_datetime_in_utc
    assert end_datetime.isoformat() == end_datetime_in_utc.isoformat()


@mock_dynamodb2
def test_inserting_recurring_schedule_sets_ical(good_scheduled_message):
    test_ical = good_scheduled_message.ical
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(good_scheduled_message)
    message = scheduler_under_test.get_messages()[0]
    ical = message.ical
    assert ical == test_ical


@mock_dynamodb2
def test_inserting_recurring_schedule_sets_message(good_scheduled_message):
    body = good_scheduled_message.body
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(good_scheduled_message)
    message = scheduler_under_test.get_messages()[0]
    actual_body = message.body
    assert actual_body == body


@mock_dynamodb2
def test_adding_blank_messages_throws_error():
    with pytest.raises(ValueError) as exception:
        ScheduledMessage(
            StartDateTimeInUtc=arrow.utcnow(),
            ical="FREQ=DAILY",
            Body="",
            PersonName="Testperson",
            EndDateTimeInUtc=datetime.datetime.utcnow() +
            datetime.timedelta(days=10))
        assert "Message body is empty" in str(exception)


@mock_dynamodb2
def test_adding_message_expiring_before_today_throws_error():
    with pytest.raises(ValueError) as exception:
        ScheduledMessage(
            StartDateTimeInUtc=arrow.utcnow(),
            ical="FREQ=DAILY",
            Body="Test Message Body",
            PersonName="Testperson",
            EndDateTimeInUtc=datetime.datetime.utcnow() -
            datetime.timedelta(days=10))
        assert "Start datetime is after end datetime" in str(exception)


@mock_dynamodb2
def test_get_next_occurence_with_daily_recurrence():
    compare_date = arrow.get('2012-01-05 03:00:00 UTC')
    m = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01:00 UTC'),
        ical="RRULE:FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.utcnow().replace(days=10))
    assert (m.is_message_ready(CompareDateTimeInUtc=compare_date))


@mock_dynamodb2
def test_get_next_occurence_with_hourly_recurrence():
    compare_date = arrow.get('2012-01-05 03:00:00 UTC')
    m = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01:00 UTC'),
        ical="RRULE:FREQ=HOURLY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.utcnow().replace(days=10))
    assert(m.is_message_ready(CompareDateTimeInUtc=compare_date))


@mock_dynamodb2
def test_get_next_occurence_with_bi_hourly_recurrence():
    m = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01:00 UTC'),
        ical="RRULE:FREQ=HOURLY;INTERVAL=2",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.utcnow().replace(days=10))
    assert m.next_occurrence_utc.year == 2012 and \
        m.next_occurrence_utc.hour == 1


@mock_dynamodb2
def test_next_occurrence_after_compare_date_not_ready():
    compare_date = arrow.get('2012-01-01 03:00:00 UTC')
    m = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01:00 UTC'),
        LastOccurrenceInUtc=arrow.get('2012-01-01 03:00:00 UTC'),
        ical="RRULE:FREQ=HOURLY;INTERVAL=2",
        Body="Test Message Body",
        PersonName="Testperson",
        CompareDateTimeInUtc=compare_date,
        EndDateTimeInUtc=arrow.utcnow().replace(days=10))
    assert not m.is_message_ready()


@mock_dynamodb2
def test_next_occurrence_after_end_datetime_is_expired():
    m = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01:00 UTC'),
        ical="RRULE:FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        LastOccurrenceInUtc=arrow.get('2012-01-02 01:01:00 UTC'),
        EndDateTimeInUtc=arrow.get('2012-01-03 00:00:01 UTC'))
    assert m.is_expired


@mock_dynamodb2
def test_next_occurrence_before_end_datetime_is_not_expired():
    m = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01:00 UTC'),
        ical="RRULE:FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        LastOccurrenceInUtc=arrow.get('2012-01-02 01:01:00 UTC'),
        EndDateTimeInUtc=arrow.get('2027-01-03 01:01:01 UTC'))
    assert not m.is_expired


@mock_dynamodb2
def test_mark_update_last_occurrence_works(good_scheduled_message):
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    test_person_name = msg.person_name
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    m = scheduler_under_test.get_messages()[0]
    spoken_time = arrow.get('2014-01-01 11:11:11 UTC')
    m.mark_spoken(spoken_time)
    scheduler_under_test.update_last_occurrence(m.uuid_key, test_person_name,
                                                spoken_time)
    assert m.last_occurrence_in_utc.year == 2014


@mock_dynamodb2
def test_set_in_queue_sets_flag(good_scheduled_message):
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    test_person_name = msg.person_name
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    m = scheduler_under_test.get_messages()[0]
    m.mark_spoken(arrow.get('2014-01-01 11:11:11 UTC'))
    scheduler_under_test.update_queue_status(m.uuid_key,
                                             test_person_name, True)
    m = scheduler_under_test.get_messages(None, False)[0]
    assert m.is_queued


@mock_dynamodb2
def test_unset_in_queue_sets_flag(good_scheduled_message):
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    test_person_name = msg.person_name
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    m = scheduler_under_test.get_messages()[0]
    m.mark_spoken(arrow.get('2014-01-01 11:11:11 UTC'))
    scheduler_under_test.update_queue_status(m.uuid_key,
                                             test_person_name, True)
    m = scheduler_under_test.get_messages(None, False)[0]
    assert m.is_queued
    scheduler_under_test.update_queue_status(m.uuid_key,
                                             test_person_name, False)
    m = scheduler_under_test.get_messages(None, False)[0]
    assert not m.is_queued


@mock_dynamodb2
def test_new_message_is_ready(good_scheduled_message):
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    m = scheduler_under_test.get_messages()[0]
    assert m.is_message_ready


@mock_dynamodb2
def test_set_in_queue_sets_message_not_ready(good_scheduled_message):
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    test_person_name = msg.person_name
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    scheduler_under_test.update_queue_status(msg.uuid_key,
                                             test_person_name, True)
    m = scheduler_under_test.get_messages(None, False)[0]
    assert m.is_queued
    assert not m.is_message_ready()


@mock_dynamodb2
def test_mark_update_last_occurrence_doesnt_get_same(good_scheduled_message):
    say_date = arrow.get('2013-01-01 01:01:01 UTC')
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))

    compare_date = say_date.replace(hours=1)
    test_person_name = msg.person_name
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    m = scheduler_under_test.get_messages(say_date, True)[0]
    m.mark_spoken(say_date)
    scheduler_under_test.update_last_occurrence(m.uuid_key, test_person_name)
    m = scheduler_under_test.get_messages(compare_date, True)
    assert len(m) == 0


@mock_dynamodb2
def test_only_get_ready_messages(good_scheduled_message):
    compare_date = arrow.utcnow().replace(hours=24)
    msg1 = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    msg2 = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2027-01-01 01:01 UTC'))
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg1)
    scheduler_under_test.schedule_message(msg2)
    m = scheduler_under_test.get_messages(compare_date, True)
    assert len(m) == 2


@mock_dynamodb2
def test_ignore_expired_messages(good_scheduled_message):
    msg = ScheduledMessage(
        StartDateTimeInUtc=arrow.get('2012-01-01 01:01 UTC'),
        ical="FREQ=DAILY",
        Body="Test Message Body",
        PersonName="Testperson",
        EndDateTimeInUtc=arrow.get('2014-01-01 01:01 UTC'))
    compare_date = arrow.utcnow()
    scheduler_under_test = Scheduler()
    scheduler_under_test.schedule_message(msg)
    m = scheduler_under_test.get_messages(compare_date, True)
    assert len(m) == 0


@mock_dynamodb2
def test_first_occurrence_is_start_date():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            ical="RRULE:FREQ=HOURLY;INTERVAL=2",
            Body="Test Message Body",
            PersonName="Testperson",
            EndDateTimeInUtc=start_date.replace(days=10))
    assert m.next_occurrence_utc == start_date


@mock_dynamodb2
def test_expiration_is_end_of_interval():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            ical="RRULE:FREQ=HOURLY;INTERVAL=2",
            Body="Test Message Body",
            PersonName="Testperson",
            EndDateTimeInUtc=start_date.replace(days=10))
    assert m.next_expiration_utc == start_date.replace(hours=2)


@mock_dynamodb2
def test_endtime_before_expiration_becomes_expiration():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    end_date = arrow.get('2012-01-01 02:00:00 UTC')
    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            ical="RRULE:FREQ=HOURLY;INTERVAL=2",
            Body="Test Message Body",
            PersonName="Testperson",
            EndDateTimeInUtc=end_date)
    assert m.next_expiration_utc == end_date


@mock_dynamodb2
def test_passing_startdate_adds_to_ical():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    ical = 'BEGIN:VEVENT\r\n' + \
        'DTSTART;VALUE=DATE-TIME:20120101T010100Z\r\n' + \
        'END:VEVENT\r\n'

    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            Body="Test",
            PersonName="test")
    assert ical == m.to_ical()


@mock_dynamodb2
def test_passing_frequency_adds_to_ical():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    ical = 'BEGIN:VEVENT\r\n' + \
        'DTSTART;VALUE=DATE-TIME:20120101T010100Z\r\n' + \
        'RRULE:FREQ=HOURLY\r\n' + \
        'END:VEVENT\r\n'

    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            Body="Test",
            Frequency='HOURLY',
            PersonName="test")
    assert ical == m.to_ical()


@mock_dynamodb2
def test_passing_enddate_adds_to_ical():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    end_date = start_date.replace(days=5)
    ical = 'BEGIN:VEVENT\r\n' + \
        'DTSTART;VALUE=DATE-TIME:20120101T010100Z\r\n' + \
        'DTEND;VALUE=DATE-TIME:20120106T010100Z\r\n' + \
        'RRULE:FREQ=HOURLY\r\n' + \
        'END:VEVENT\r\n'

    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            EndDateTimeInUtc=end_date,
            Body="Test",
            Frequency='HOURLY',
            PersonName="test")
    assert ical == m.to_ical()


@mock_dynamodb2
def test_passing_count_adds_to_ical():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    end_date = start_date.replace(days=5)
    ical = 'BEGIN:VEVENT\r\n' + \
        'DTSTART;VALUE=DATE-TIME:20120101T010100Z\r\n' + \
        'DTEND;VALUE=DATE-TIME:20120106T010100Z\r\n' + \
        'RRULE:FREQ=HOURLY;COUNT=10\r\n' + \
        'END:VEVENT\r\n'

    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            EndDateTimeInUtc=end_date,
            Count=10,
            Body="Test",
            Frequency='HOURLY',
            PersonName="test")
    assert ical == m.to_ical()


@mock_dynamodb2
def test_passing_interval_adds_to_ical():
    start_date = arrow.get('2012-01-01 01:01:00 UTC')
    end_date = start_date.replace(days=5)
    ical = 'BEGIN:VEVENT\r\n' + \
        'DTSTART;VALUE=DATE-TIME:20120101T010100Z\r\n' + \
        'DTEND;VALUE=DATE-TIME:20120106T010100Z\r\n' + \
        'RRULE:FREQ=HOURLY;COUNT=10;INTERVAL=5\r\n' + \
        'END:VEVENT\r\n'

    m = ScheduledMessage(
            StartDateTimeInUtc=start_date,
            EndDateTimeInUtc=end_date,
            Count=10,
            Body="Test",
            Frequency='HOURLY',
            Interval=5,
            PersonName="test")
    assert ical == m.to_ical()
