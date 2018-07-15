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
from person.person import Person, PersonManager
import pytest
from mock import patch, MagicMock

rpi_mock = MagicMock()
modules = {
        "RPi": rpi_mock,
        "RPi.GPIO": rpi_mock.GPIO,
}

patcher = patch.dict("sys.modules", modules)
patcher.start()

from locator.locator import LocationAvailability, TimeWindow
from locator.locator import LocationStatus, LocationManager, \
    LocationVerification

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

verify_location_response = {
     'slotToElicit': None,
     'dialogState': 'ReadyForFulfillment',
     'intentName': 'VerifyPersonLocationIntent',
     'responseCard': None,
     'message': None,
     'slots': {
         'Person': 'Calvin'
     },
     'sessionAttributes': {}
}

invalid_user_response = {
    'message': 'No usable messages given the current slot and ' +
    'sessionAttribute set.'
}

cannot_understand_response = {
    'x-amz-lex-message': 'Sorry, I could not understand.  Goodbye.',
    'x-amzn-requestid': 'e79eacec-e950-11e6-b46e-e3155774eb28',
    'x-amz-lex-dialog-state': 'Failed',
    'x-amz-lex-session-attributes': 'e30=',
    'content-length': '0',
    'connection': 'keep-alive',
    'x-amz-lex-slots': 'eyJQZXJzb24iOiJDYWx2aW4ifQ==',
    'date': 'Thu, 02 Feb 2017 14:07:22 GMT',
    'content-type': 'text/plain;charset=utf-8',
    'x-amz-lex-intent-name': 'VerifyPersonLocationIntent'
}

user_confirmed_response = {
    'x-amz-lex-message': 'Calvin confirmed',
    'x-amzn-requestid': 'f34af53d-e950-11e6-b18e-c591277bc19d',
    'x-amz-lex-dialog-state': 'ConfirmIntent',
    'x-amz-lex-session-attributes': 'e30=',
    'content-length': '0',
    'connection': 'keep-alive',
    'x-amz-lex-slots': 'eyJQZXJzb24iOiJDYWx2aW4ifQ==',
    'date': 'Thu, 02 Feb 2017 14:07:41 GMT',
    'content-type': 'text/plain;charset=utf-8',
    'x-amz-lex-intent-name': 'VerifyPersonLocationIntent'}


def test_create_time_window_with_priority_sets_priority():
    l = TimeWindow(Priority=100, ical=ical_event)
    assert l.priority == 100


def test_creating_with_location_name_sets_name():
    l = LocationAvailability(LocationName="test_name",
                             Priority=100, ical=ical_event)
    assert l.location_name == "test_name"


def test_creating_with_ical_sets_ical():
    tw = TimeWindow(Priority=100, ical=ical_event)
    assert tw.ical == ical_event


def test_previous_start_returns_correct_value():
    now_dt = arrow.get('2014-01-01T01:01:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    start = tw.previous_start()
    assert start == arrow.get('2013-12-31 07:12:00-05:00')


def test_time_outside_window_is_not_available():
    now_dt = arrow.get('2014-01-01T06:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    l = LocationAvailability()
    l.add_window(tw)
    assert not l.is_available(dt=now_dt)


def test_window_set_with_muted_window_is_not_available():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event_night, CompareDateTime=now_dt)
    l = LocationAvailability(LocationName='kitchen')
    l.add_window(tw)
    tw_night = TimeWindow(ical=ical_event, CompareDateTime=now_dt,
                          IsMuted=True)
    l.add_window(tw_night)
    assert not l.is_available(dt=now_dt)


def test_window_set_with_off_window_muted_window_is_available():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    tw_night = TimeWindow(ical=ical_event_night, CompareDateTime=now_dt)
    l = LocationAvailability(LocationName='kitchen')
    l.add_window(tw)
    tw_night = TimeWindow(ical=ical_event_night, CompareDateTime=now_dt,
                          IsMuted=True)
    l.add_window(tw_night)
    assert l.is_available(dt=now_dt)


def test_time_inside_window_is_available():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    l = LocationAvailability()
    l.add_window(tw)
    assert l.is_available(dt=now_dt)


def test_can_add_window():
    l = LocationAvailability()
    tw = TimeWindow(ical=ical_event)
    l.add_window(tw)
    assert len(l.time_windows.set_list) == 1


def test_time_window_defaults_to_unmuted():
    l = LocationAvailability()
    tw = TimeWindow(ical=ical_event)
    l.add_window(tw)
    assert not l.time_windows.set_list[0].is_muted


def test_can_add_muted_window():
    l = LocationAvailability()
    tw = TimeWindow(ical=ical_event, IsMuted=True)
    l.add_window(tw)
    assert l.time_windows.set_list[0].is_muted


def test_setting_location_status_name_sets_location():
    l = LocationStatus(Name='test')
    assert l.name == 'test'


def test_setting_last_heartbeat_sets_heartbeat():
    now_dt = arrow.utcnow()
    l = LocationStatus(LastHeartbeat=now_dt)
    assert l.last_heartbeat_dt == now_dt


@mock_dynamodb2
def test_mute_location_mutes_location():
    lm = LocationManager()
    lm.toggle_mute('kitchen', True)
    loc = lm.get_location('kitchen')
    assert loc.is_muted


@mock_dynamodb2
def test_unmute_location_unmutes_location():
    lm = LocationManager()
    lm.toggle_mute('kitchen', True)
    loc = lm.get_location('kitchen')
    assert loc.is_muted
    lm.toggle_mute('kitchen', False)
    loc = lm.get_location('kitchen')
    assert not loc.is_muted


@mock_dynamodb2
def test_saving_window_set_saves_set():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    la = LocationAvailability(LocationName='kitchen')
    la.add_window(tw)
    tw = TimeWindow(IsMuted=True, ical=ical_event, CompareDateTime=now_dt)
    la.add_window(tw)
    lm = LocationManager()
    lm.update_window_set(la)
    loc = lm.get_location('kitchen')
    assert loc.time_windows.count() == 2


@mock_dynamodb2
def test_db_window_set_with_off_window_muted_window_is_available():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    tw_night = TimeWindow(ical=ical_event_night, CompareDateTime=now_dt)
    l = LocationAvailability(LocationName='kitchen')
    l.add_window(tw)
    tw_night = TimeWindow(IsMuted=True,
                          ical=ical_event_night, CompareDateTime=now_dt)
    l.add_window(tw_night)
    lm = LocationManager()
    lm.update_window_set(l)
    l = lm.get_location('kitchen')
    assert l.is_available(dt=now_dt)


@mock_dynamodb2
def test_db_window_set_with_muted_window_is_not_available():
    now_dt = arrow.get('2014-01-01T09:09:00.000-05:00')
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt)
    l = LocationAvailability(LocationName='kitchen')
    l.add_window(tw)
    tw = TimeWindow(ical=ical_event, CompareDateTime=now_dt, IsMuted=True)
    l.add_window(tw)
    lm = LocationManager()
    lm.update_window_set(l)
    l = lm.get_location('kitchen')
    assert not l.is_available(dt=now_dt)


@mock_dynamodb2
def test_setting_local_button_sets_local_button():
    l = LocationAvailability(LocationName='kitchen')
    l.with_switch(Color='Red',
                  Name='Test',
                  Style='Circle')
    assert len(list(l.input_capabilities.keys())) == 1


@mock_dynamodb2
def test_setting_local_button_color_sets_color():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    assert l.input_capabilities[id]['color'] == 'Red'


@mock_dynamodb2
def test_setting_local_button_name_sets_name():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    assert l.input_capabilities[id]['name'] == 'Test'


@mock_dynamodb2
def test_setting_local_button_style_sets_style():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    assert l.input_capabilities[id]['style'] == 'Circle'


@mock_dynamodb2
def test_updating_existing_switch_does_not_add_new_switch():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    assert id in list(l.input_capabilities.keys()) and \
        l.input_capabilities[id]['style'] == 'Circle'

    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Square')
    assert len(list(l.input_capabilities.keys())) == 1 and \
        l.input_capabilities[id]['style'] == 'Square'


@mock_dynamodb2
def test_saving_switch_saves_color():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    lm = LocationManager()
    lm.update_input_capabilities(l)
    loc = lm.get_location('kitchen')
    assert loc.input_capabilities[id]['color'] == 'Red'


@mock_dynamodb2
def test_saving_switch_saves_name():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    lm = LocationManager()
    lm.update_input_capabilities(l)
    loc = lm.get_location('kitchen')
    assert loc.input_capabilities[id]['name'] == 'Test'


@mock_dynamodb2
def test_saving_switch_saves_style():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    lm = LocationManager()
    lm.update_input_capabilities(l)
    loc = lm.get_location('kitchen')
    assert loc.input_capabilities[id]['style'] == 'Circle'


@mock_dynamodb2
def test_saving_switch_saves_id():
    l = LocationAvailability(LocationName='kitchen')
    id = 'myswitch'
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    lm = LocationManager()
    lm.update_input_capabilities(l)
    loc = lm.get_location('kitchen')
    assert id in list(loc.input_capabilities.keys())


@patch('babylex.LexSession.text')
def test_can_send_verify_location_request(text_mock):
    text_mock.return_value = verify_location_response
    lv = LocationVerification(LocationName='room', PersonName='calvin')
    assert lv.verify_valid_user()


@patch('babylex.LexSession.text')
def test_bad_invalid_person_throws_error(text_mock):
    text_mock.return_value = invalid_user_response
    lv = LocationVerification(LocationName='room', PersonName='calvin')

    with pytest.raises(ValueError) as exc:
        assert lv.verify_valid_user()

    assert 'Person does not exist' in str(exc.value)


@patch('babylex.LexSession.text')
def test_confirm_user_location_returns_true(text_mock):
    text_mock.return_value = user_confirmed_response
    lv = LocationVerification(LocationName='room', PersonName='calvin')
    resp = lv.send_confirm_response(TextResponse='OK')
    assert resp == 'Confirmed'


@patch('babylex.LexSession.text')
def test_confirm_invalid_user_location_returns_not_understood(text_mock):
    text_mock.return_value = cannot_understand_response
    lv = LocationVerification(LocationName='room', PersonName='calvin')
    resp = lv.send_confirm_response(TextResponse='asdasdsdasd')
    assert resp == 'NotUnderstood'


@patch('babylex.LexSession.text')
def test_no_confirm_user_location_queues_next_location(text_mock):
    text_mock.return_value = invalid_user_response
    assert False


@patch('babylex.LexSession.text')
def test_no_confirm_user_location_with_no_more_locs_drops_msg(text_mock):
    text_mock.return_value = invalid_user_response
    assert False


@patch('person.person.PersonManager.get_person')
@mock_dynamodb2
def test_location_verify_sets_person(p_mock):
    p = Person(Name='calvin')
    p.require_physical_confirmation = True
    p_mock.return_value = p
    lv = LocationVerification(LocationName='room', PersonName='calvin')
    assert p.name == lv.person_name


@patch('person.person.PersonManager.get_person')
@mock_dynamodb2
def test_person_req_phys_conf_sets_req_phys_conf_for_loc_verify(p_mock):
    pm = PersonManager()
    p = Person(Name='calvin')
    p.require_physical_confirmation = True
    pm.update_window_set(p)
    lv = LocationVerification(LocationName='room', PersonName='calvin')
    assert lv.person.require_physical_confirmation


@mock_dynamodb2
def test_verify_switch_with_press_returns_true():
    rpi_mock.GPIO.setmode.return_value = None
    rpi_mock.GPIO.setup.return_value = None
    rpi_mock.GPIO.input.return_value = False
    pm = PersonManager()
    p = Person(Name='calvin')
    p.require_physical_confirmation = True
    pm.update_window_set(p)
    l = LocationAvailability(LocationName='kitchen')
    id = 12
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    lm = LocationManager()
    lm.update_input_capabilities(l)
    lv = LocationVerification(LocationName='kitchen',
                              PersonName='calvin')

    done, count, timeout = lv.verify_person_at_location()
    print((done, count, timeout))
    assert done and count == 1 and timeout < 3


@mock_dynamodb2
def test_verify_switch_with_no_press_returns_false():
    rpi_mock.GPIO.setmode.return_value = None
    rpi_mock.GPIO.setup.return_value = None
    rpi_mock.GPIO.input.return_value = True
    pm = PersonManager()
    p = Person(Name='calvin')
    p.require_physical_confirmation = True
    pm.update_window_set(p)
    l = LocationAvailability(LocationName='kitchen')
    id = 12
    l.with_switch(HardwareId=id,
                  Color='Red',
                  Name='Test',
                  Style='Circle')
    lm = LocationManager()
    lm.update_input_capabilities(l)
    lv = LocationVerification(LocationName='kitchen',
                              PersonName='calvin',
                              TimeoutInSeconds=2,
                              RetryCount=2)

    done, count, timeout = lv.verify_person_at_location()
    assert not done and count == 2 and timeout >= 2 and timeout < 3
