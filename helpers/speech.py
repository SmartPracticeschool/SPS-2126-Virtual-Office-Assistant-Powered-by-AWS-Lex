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
from helpers.weather import Weather


class SpeechHelper(object):
    def __init__(self, **kwargs):
        self.person = kwargs.get('PersonName', '')

    def replace_tokens(self, msg):
        msg = msg.replace('{person}', self.person)
        msg = msg.replace('{greeting}', self.greeting())

        if '{weather}' in msg:
            w = Weather()
            msg = msg.replace('{weather}', w.describe())
        msg = msg.replace('{datetime}', self.time_and_date())
        return msg

    def time_and_date(self):
        d = arrow.utcnow().format('dddd, MMMM DD, YYYY')
        return "Today is {}.".format(d)

    def greeting(self):
        d = arrow.now()
        if d.hour < 12:
            tod = "morning"
        elif 12 <= d.hour < 18:
            tod = "afternoon"
        else:
            tod = "evening"

        return "Good {}, {}.".format(tod, self.person)
