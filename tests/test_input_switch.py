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

from mock import patch, MagicMock

rpi_mock = MagicMock()
modules = {
        "RPi": rpi_mock,
        "RPi.GPIO": rpi_mock.GPIO,
}

patcher = patch.dict("sys.modules", modules)
patcher.start()

from input.switch import Switch


def test_switch_id_sets_on_creation():
    s = Switch(HardwareId=10)
    assert s.id == 10


def test_switch_name_sets_on_creation():
    name = 'blue button'
    s = Switch(HardwareId=10, Name=name)
    assert s.name == name


def test_switch_timeout_sets_on_creation():
    timeout_in_secs = 15
    s = Switch(TimeoutInSeconds=timeout_in_secs,
               HardwareId=10)
    assert s.timeout_in_secs == timeout_in_secs


def test_no_switch_input_times_out():
    rpi_mock.GPIO.setmode.return_value = None
    rpi_mock.setup.return_value = None
    rpi_mock.input.return_value = True
    timeout_in_secs = 3
    s = Switch(TimeoutInSeconds=timeout_in_secs,
               HardwareId=10)
    done, timeout = s.wait_for_input()
    assert not done and timeout >= 3 and timeout < 4


def test_switch_input_returns_true():
    rpi_mock.GPIO.setmode.return_value = None
    rpi_mock.GPIO.setup.return_value = None
    rpi_mock.GPIO.input.return_value = False
    timeout_in_secs = 3
    s = Switch(TimeoutInSeconds=timeout_in_secs,
               HardwareId=10)
    done, timeout = s.wait_for_input()
    assert done and timeout < 3
