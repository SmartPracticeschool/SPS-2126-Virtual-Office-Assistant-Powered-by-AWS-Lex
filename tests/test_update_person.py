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

from lambda_functions.update_person import handler
from moto import mock_dynamodb2
from person.person import PersonManager
import pytest


ctx = {}
calvin_name = 'calvin'
window_set = """
[
    {
        "IsMuted":false,
        "Priority":100,
        "ICal":"\nBEGIN:VEVENT\nDTSTART;TZID=EST;VALUE=DATE-TIME:20170101T170000\nDURATION:PT4H\nRRULE:FREQ=DAILY\nEND:VEVENT\n",
        "LocationName":"media_room"
    },
    {
        "IsMuted":false,
        "Priority":100,
        "ICal":"\nBEGIN:VEVENT\nDTSTART;TZID=EST;VALUE=DATE-TIME:20170101T090000\nDURATION:PT11H\nRRULE:FREQ=WEEKLY;BYDAY=SA,SU\nEND:VEVENT\n",
        "LocationName":"media_room"
    }
]
"""


@mock_dynamodb2
def test_updating_name_only_add_name_only():
    event = {'message': {'Name': calvin_name}}
    handler(event, ctx)
    pm = PersonManager()
    p = pm.get_person(calvin_name)
    assert p.name == calvin_name


@mock_dynamodb2
def test_add_with_phys_conf_sets_true():
    event = {'message': {'Name': calvin_name,
                         'RequirePhysicalConfirmation': True}}
    handler(event, ctx)
    pm = PersonManager()
    p = pm.get_person(calvin_name)
    assert p.require_physical_confirmation


@mock_dynamodb2
def test_add_with_false_phys_conf_sets_false():
    event = {'message': {'Name': calvin_name,
                         'RequirePhysicalConfirmation': False}}
    handler(event, ctx)
    pm = PersonManager()
    p = pm.get_person(calvin_name)
    assert not p.require_physical_confirmation


@mock_dynamodb2
def test_add_with_no_phys_conf_sets_false():
    event = {'message': {'Name': calvin_name}}
    handler(event, ctx)
    pm = PersonManager()
    p = pm.get_person(calvin_name)
    assert not p.require_physical_confirmation


@mock_dynamodb2
def test_no_name_throws_error():
    event = {'message': {'Nam': calvin_name}}

    with pytest.raises(ValueError) as e:
        handler(event, ctx)
    assert("Missing value for 'Name'" in str(e.value))


@mock_dynamodb2
def test_with_window_set_saves():
    event = {'message': {'Name': calvin_name,
                         'WindowSet': window_set}}
    handler(event, ctx)
    pm = PersonManager()
    p = pm.get_person(calvin_name)
    assert p.time_windows.count() == 2
