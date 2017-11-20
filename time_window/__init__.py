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

from icalendar import Calendar
from dateutil.rrule import rrulestr
import arrow
import json
from helpers.datetime_helpers import check_if_timezone_naive

LOCATION_TABLE = 'locations'


def display(cal):
    return cal.to_ical().replace('\r\n', '\n').strip()


class TimeWindowSet(object):
    def __init__(self):
        self.set_list = []

    def add_time_window(self, tw):
        self.set_list.append(tw)

    def is_available(self, dt):
        is_avail = False
        print "Checking if window is current with " + dt.isoformat()
        for tw in self.set_list:
            print 'is it muted? ' + str(tw.is_muted)
            print "is in window " + str(tw.is_in_window(dt))
            if tw.is_muted and tw.is_in_window(dt):
                print "NOT AVAILABLE"
                return False
            if tw.is_in_window(dt):
                print "AVAILABLE"
                is_avail = True
        return is_avail

    def to_json(self):
        return json.dumps([dict(tw.to_json())
                           for tw in self.set_list])

    def count(self):
        return len(self.set_list)

    def set_compare_date(self, compare_dt):
        for w in self.set_list:
            w.compare_date = compare_dt

    def all_available(self, dt=None):
        if not dt:
            dt = arrow.utcnow()
        for tw in self.set_list:
            if not tw.is_muted and tw.is_in_window(dt):
                yield tw


class TimeWindow(object):
    def __init__(self, **kwargs):
        self.ical = kwargs.get('ical', '')
        self.is_muted = kwargs.get('IsMuted', False)
        self.compare_dt = kwargs.get('CompareDateTime', None)
        self.priority = kwargs.get('Priority', False)
        try:
            ev = Calendar.from_ical(self.ical)
            start = arrow.get(ev.get('dtstart').dt)
            self.delta = ev.get('duration').dt
            check_if_timezone_naive(start, 'start')
            self.rule = rrulestr(ev.get('rrule').to_ical(),
                                 dtstart=start.datetime)
        except Exception as ex:
            raise ValueError("Error processing ical: %s" % str(ex))

    def previous_start(self, dt=None):
        if not dt and self.compare_dt:
            dt = self.compare_dt
        return self.rule.before(dt, inc=True)

    def previous_end(self, dt=None):
        if not dt and self.compare_dt:
            dt = self.compare_dt
        return self.previous_start(dt) + self.delta

    def is_in_window(self, dt=None):
        if not dt:
            dt = arrow.utcnow()
        return self.previous_start(dt) < dt < self.previous_end(dt)

    def to_json(self):
        return {'ical': self.ical,
                'is_muted': self.is_muted,
                'priority': self.priority
                }
