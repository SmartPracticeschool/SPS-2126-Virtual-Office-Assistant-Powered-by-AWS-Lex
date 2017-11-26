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

"""
the message object
"""
import uuid
import arrow
from dateutil.rrule import rrulestr
from helpers.datetime_helpers import check_if_timezone_naive
from icalendar import Event, Calendar
import logging


class ScheduledMessage(object):
    def __init__(self, **kwargs):
        self.uuid_key = kwargs.pop("UUID", str(uuid.uuid4()))
        self.start_datetime_in_utc = kwargs.pop("StartDateTimeInUtc", "")
        self.ical = kwargs.pop("ical", "")
        self.person_name = kwargs.pop("PersonName", "")
        self.end_datetime_in_utc = kwargs.pop("EndDateTimeInUtc", "")
        self.body = kwargs.pop("Body", "")
        self.is_queued = kwargs.pop("IsQueued", False)
        self.last_loc = kwargs.pop("LastLocationIndex", False)
        self.expired = kwargs.pop("IsExpired", False)
        self.compare_datetime_in_utc = kwargs.pop("CompareDateTimeInUtc", "")
        self.last_occurrence_in_utc = kwargs.pop("LastOccurrenceInUtc",
                                                 None)
        self.no_more_occurrences = str(self.next_occurrence_utc) == 'N/A'
        self.frequency = kwargs.pop("Frequency", "")
        self.count = kwargs.pop("Count", "")
        self.interval = kwargs.pop("Interval", "")
        self.lexbot = kwargs.pop("Lexbot", "")
        self.timezone = kwargs.pop('TimeZone', "local")
        self.bot_names = kwargs.pop('BotNames', "")
        self.required_bots = kwargs.pop("RequiredBots", "")
        self.ice_breaker = kwargs.pop("IceBreaker", "")

        if (self.last_occurrence_in_utc):
            check_if_timezone_naive(self.last_occurrence_in_utc,
                                    "last_occurrence_in_utc")
        check_if_timezone_naive(self.start_datetime_in_utc,
                                "start_datetime_in_utc")
        if self.end_datetime_in_utc:
            check_if_timezone_naive(self.end_datetime_in_utc,
                                    "end_datetime_in_utc")
            if self.start_datetime_in_utc > self.end_datetime_in_utc:
                raise ValueError("Start datetime is after end datetime")
        if (not self.body):
            raise ValueError("Message body is empty")
        logging.debug(self.__str__())

    def to_ical(self):
        if self.ical:
            return self.ical
        else:
            ev = Event()
            rrule = {}
            ev.add('dtstart', self.start_datetime_in_utc.datetime)
            if self.end_datetime_in_utc:
                ev.add('dtend', self.end_datetime_in_utc.datetime)
            if self.count:
                rrule['count'] = self.count
            if self.interval:
                rrule['interval'] = self.interval
            if self.frequency:
                rrule['freq'] = self.frequency
            if rrule:
                ev.add('rrule', rrule)
            return ev.to_ical()

    def __str__(self):
        last_occurrence = None
        if not self.last_occurrence_in_utc:
            last_occurrence = "Never"
        return "\n".join([
            '',
            'uuid_key: %s' % self.uuid_key,
            'person_name: %s' % self.person_name,
            'start_time (UTC): %s' % self.start_datetime_in_utc,
            'start_time (local): %s' % self.start_datetime_in_utc.to('local'),
            'end_time (UTC): %s' % self.end_datetime_in_utc or None,
            'end_time (local): %s' % self.end_datetime_local or None,
            'last_occurrence (UTC): %s' % (last_occurrence or
                                           self.last_occurrence_in_utc),
            'last_occurrence (local): %s' % (last_occurrence or
                                             self.last_occurrence_in_utc
                                             .to('local')),
            'next_occurrence (UTC): %s' % self.next_occurrence_utc,
            'next_occurrence (local): %s'
            % self.next_occurrence_local,
            'next_expiration (UTC): %s' % self.next_expiration_utc,
            'next_expiration (local): %s'
            % self.next_expiration_local,
            'is_expired: %s' % self.is_expired,
            'is_ready: %s' % self.is_message_ready(),
            'is_queued: %s' % self.is_queued,
            'body: %s' % self.body
        ])

    @property
    def start_datetime_local(self):
        if self.start_datetime_in_utc:
            return self.start_datetime_in_utc.to('local')
        else:
            return None

    @property
    def end_datetime_local(self):
        if self.end_datetime_in_utc:
            return self.end_datetime_in_utc.to('local')
        else:
            return None

    @property
    def next_occurrence_utc(self):
        next_occur, expires = self.next_occurrence()
        return next_occur

    @property
    def next_expiration_utc(self):
        next_occur, expires = self.next_occurrence()
        return expires

    @property
    def next_occurrence_local(self):
        next_occur = self.next_occurrence_utc
        if next_occur == 'N/A':
            return 'N/A'
        return arrow.get(next_occur).to('local')

    @property
    def last_occurrence_local(self):
        if self.last_occurrence_in_utc:
            return self.last_occurrence_in_utc.to('local')
        else:
            return None

    @property
    def next_expiration_local(self):
        next_occur, expires = self.next_occurrence()
        return arrow.get(expires).to('local')

    @property
    def is_expired(self):
        if not self.end_datetime_in_utc:
            return False
        if self.no_more_occurrences:
            return False
        if (self.next_occurrence_utc > self.end_datetime_in_utc) or \
           (self.end_datetime_in_utc < arrow.utcnow()):
            return True
        else:
            return False

    def next_occurrence(self):
        # if not messages have been queued yet, then the next occurrence
        # is the start time
        next_occur = None
        if (not self.last_occurrence_in_utc):
            next_occur = self.start_datetime_in_utc.datetime
            next_expire = arrow.get(next_occur).replace(minutes=+10)
            if self.end_datetime_in_utc < next_expire:
                next_expire = self.end_datetime_in_utc
            return next_occur, next_expire
        else:
            start = self.start_datetime_in_utc.datetime
            if self.ical == 'VEVENT':
                cal = Calendar.from_ical(self.ical)
                for component in cal.walk():
                    if component.name == 'VEVENT':
                        rrule = component.get('RRULE').to_ical().decode('utf-8')
            else:
                rrule = self.ical
            rule = rrulestr(rrule, dtstart=start)
            next_after_now = rule.after(self.compare_datetime_in_utc or
                                        arrow.utcnow().datetime)
            if not next_after_now:
                logging.info('No next_after_now, so next_occur=N/A')
                return 'N/A', self.compare_datetime_in_utc or arrow.utcnow()
            next_before_now = rule.before(next_after_now)
            if next_before_now and \
                    (self.last_occurrence_in_utc > next_before_now):
                next_occur = next_after_now
            else:
                next_occur = next_before_now
        rule = rrulestr(rrule, dtstart=next_occur)
        expires = rule.after(next_occur)
        if not expires:
            return 'N/A', arrow.utcnow().replace(minutes=+10)
        if (expires > self.end_datetime_in_utc):
            expires = self.end_datetime_in_utc
        return arrow.get(next_occur), arrow.get(expires)

    def is_message_ready(self, **kwargs):
        if self.is_expired or self.is_queued:
            print 'Expired = {}, Queued = {}'.format(
                    self.is_expired,
                    self.is_queued)
            return False

        next_occur, expires = self.next_occurrence()
        if next_occur == 'N/A':
            return True
        print self.compare_datetime_in_utc
        compare_datetime = self.compare_datetime_in_utc or arrow.utcnow()
        print 'self.end_datetime: {}'.format(self.end_datetime_in_utc)
        print 'next: {}'.format(next_occur)
        print 'compare_datetime= {}'.format(compare_datetime)
        print 'next <= compare: {}'.format(next_occur <= compare_datetime)
        if next_occur <= compare_datetime:
            if self.end_datetime_in_utc and \
                    self.end_datetime_in_utc <= next_occur:
                        return False
            else:
                return True

    def mark_spoken(self, spoken_datetime=None):
        if not spoken_datetime:
            spoken_datetime = arrow.utcnow()
        self.last_occurrence_in_utc = spoken_datetime


class QueuedMessage(object):
    def __init__(self, **kwargs):
        queued_message = kwargs.pop("QueuedMessage")
        if queued_message.message_attributes is not None:
            ma = queued_message.message_attributes
            try:
                self.uuid_key = queued_message.message_attributes \
                    .get('UUID').get('StringValue')
            except ValueError:
                raise ValueError("Missing uuid from queued message")
            expiration_date = queued_message.message_attributes \
                .get('ExpirationDateTimeInUtc').get('StringValue')
            self.no_more_occurrences = bool(queued_message.message_attributes
                                            .get('NoMoreOccurrences')
                                            .get('StringValue'))
            if ma.get('IceBreaker'):
                self.ice_breaker = queued_message.message_attributes \
                    .get('IceBreaker').get('StringValue')
            else:
                self.ice_breaker = ""

            if ma.get('BotNames'):
                self.bot_names = queued_message.message_attributes \
                    .get('BotNames').get('StringValue')
            else:
                self.bot_names = ''

            if ma.get('RequiredBots'):
                self.required_bots = queued_message.message_attributes \
                    .get('RequiredBots').get('StringValue')
            else:
                self.required_bots = ''

            self.voice_id = queued_message.message_attributes \
                .get('Voice').get('StringValue')
            person_name = queued_message.message_attributes \
                .get('PersonName').get('StringValue')
            self.person_name = person_name
            try:
                if expiration_date:
                    self.expiration_datetime_in_utc = \
                        arrow.get(expiration_date)
            except ValueError:
                raise ValueError("Unable to parse expiration date")
        self.body = queued_message.body
        if self.expiration_datetime_in_utc < arrow.utcnow():
            print "%s < %s:%s" % (self.expiration_datetime_in_utc,
                                  arrow.utcnow(), True)
            self.is_expired = True
        else:
            print "%s>%s:%s" % (self.expiration_datetime_in_utc,
                                arrow.utcnow(), False)
            self.is_expired = False
        self.original_message = kwargs.get("Message", "")

    def __str__(self):
        return "\n".join([
            '',
            'expire (UTC): %s' % self.expiration_datetime_in_utc,
            'is_expired: %s' % self.is_expired
        ])
