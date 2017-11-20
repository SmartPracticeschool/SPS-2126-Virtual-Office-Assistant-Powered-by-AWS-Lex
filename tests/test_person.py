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
from moto import mock_dynamodb2
from person.person import Person, PersonTimeWindow, PersonManager

ical_event_night = """
BEGIN:VEVENT
DTSTART;TZID=EST;VALUE=DATE-TIME:20131122T221200
DURATION:PT6H
RRULE:FREQ=DAILY
END:VEVENT
"""

ical_event = """
BEGIN:VEVENT
DTSTART;TZID=EST;VALUE=DATE-TIME:20131122T071200
DURATION:PT6H
RRULE:FREQ=DAILY
END:VEVENT
"""

ical_event_before_school = """
BEGIN:VEVENT
DTSTART;TZID=EST;VALUE=DATE-TIME:20131122T070000
DURATION:PT1H
RRULE:FREQ=DAILY
END:VEVENT
"""


def test_create_person_with_name_sets_name():
    p = Person(Name='Calvin')
    assert p.name == 'Calvin'


def test_create_person_time_window_with_priority_sets_priority():
    ptw = PersonTimeWindow(Priority=100, ical=ical_event)
    assert ptw.priority == 100


def test_creating_with_location_name_sets_name():
    ptw = PersonTimeWindow(LocationName="test_name",
                           Priority=100, ical=ical_event)
    assert ptw.location_name == "test_name"


def test_creating_with_ical_sets_ical():
    tw = PersonTimeWindow(Priority=100, ical=ical_event)
    assert tw.ical == ical_event


def test_previous_start_returns_correct_value():
    now_dt = arrow.get('2014-01-01T01:01:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen',
                          ical=ical_event, CompareDateTime=now_dt)
    start = tw.previous_start()
    assert start == arrow.get('2013-12-31 07:12:00-05:00')


def test_add_multiple_returns_correct_number():
    p = Person(Name='calvin')
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    assert p.all_available_count(now_dt) == 2


@mock_dynamodb2
def test_mute_person_mutes_person():
    pm = PersonManager()
    pm.toggle_mute('calvin', True)
    p = pm.get_person('calvin')
    assert p.is_muted


@mock_dynamodb2
def test_unmute_person_unmutes_person():
    pm = PersonManager()
    pm.toggle_mute('calvin', True)
    p = pm.get_person('calvin')
    assert p.is_muted
    pm.toggle_mute('calvin', False)
    p = pm.get_person('calvin')
    assert not p.is_muted


@mock_dynamodb2
def test_saving_person_window_set_saves_set():
    pm = PersonManager()
    p = Person(Name='calvin')
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)

    pm.update_window_set(p)
    p = pm.get_person('calvin')
    assert p.time_windows.count() == 2


@mock_dynamodb2
def test_saving_person_with_available_windows_are_available():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    pm = PersonManager()
    p = Person(Name='calvin')
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event, CompareDateTime=now_dt)
    p.add_window(tw)

    pm.update_window_set(p)
    assert p.all_available_count(now_dt) == 2


@mock_dynamodb2
def test_preference_is_sorted_correctly():
    pm = PersonManager()
    p = Person(Name='calvin')
    now_dt = arrow.get('2014-01-01T07:10:00.000-05:00')
    tw = PersonTimeWindow(LocationName='kitchen', Priority=100,
                          ical=ical_event_before_school,
                          CompareDateTime=now_dt)
    p.add_window(tw)
    tw = PersonTimeWindow(LocationName='bedroom', Priority=200,
                          ical=ical_event_before_school,
                          CompareDateTime=now_dt)
    p.add_window(tw)
    pm.update_window_set(p)
    assert p.all_available(now_dt)[0].priority == 200
    assert p.all_available(now_dt)[1].priority == 100
    tw = PersonTimeWindow(LocationName='mediaroom', Priority=50,
                          ical=ical_event_before_school,
                          CompareDateTime=now_dt)
    p.add_window(tw)
    pm.update_window_set(p)
    p = pm.get_person('calvin')
    assert p.all_available(now_dt)[0].priority == 200
    assert p.all_available(now_dt)[1].priority == 100
    assert p.all_available(now_dt)[2].priority == 50


@mock_dynamodb2
def test_can_save_physical_confirmation_true_preference():
    pm = PersonManager()
    p = Person(Name='calvin')
    p.require_physical_confirmation = True
    pm.update_window_set(p)
    p = pm.get_person('calvin')
    assert p.require_physical_confirmation


@mock_dynamodb2
def test_can_save_physical_confirmation_false_preference():
    pm = PersonManager()
    p = Person(Name='calvin')
    p.require_physical_confirmation = False
    pm.update_window_set(p)
    p = pm.get_person('calvin')
    assert not p.require_physical_confirmation
