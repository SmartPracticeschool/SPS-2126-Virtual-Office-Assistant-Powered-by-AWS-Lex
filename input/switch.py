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

# import RPi.GPIO as GPIO
import arrow
import time


class Switch(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('Name')
        self.id = int(kwargs.get('HardwareId'))
        self.timeout_in_secs = kwargs.get('TimeoutInSeconds')

    def wait_for_input(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.id, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        start = arrow.utcnow()
        done = False
        print(('waiting for input on ' + str(self.id)))
        while not done and \
                (arrow.utcnow() - start).seconds < self.timeout_in_secs:
            input_state = GPIO.input(self.id)
            print(input_state)
            if input_state == 0:
                done = True
            time.sleep(0.1)
        return done, (arrow.utcnow() - start).seconds
