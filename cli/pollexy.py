#!/usr/bin/python
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

import click
from messages.message import ScheduledMessage
from messages.message_manager import MessageManager, LibraryManager
from scheduler.scheduler import Scheduler
from speaker.speaker import Speaker
from cache.cache_manager import CacheManager
from person.person import PersonManager
from face.face import FaceManager
from locator.locator import LocationManager, LocationVerification
from helpers.config import ConfigHelper
import random
import arrow
import logging
import traceback
import os
import sys
import json
from ConfigParser import SafeConfigParser
from python_terraform import Terraform
from subprocess import call
from lex import LexBotManager, LexIntentManager, LexSlotManager, LexPlayer

logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s - %(levelname)s'
                    '- %(message)s')


class Config():
    def __init__(self):
        self.value = 777


def say(**kwargs):
    msg = kwargs.get('Message')
    voice = kwargs.get('VoiceId', 'Joanna')
    include_chime = kwargs.get('IncludeChime', True)
    s = Speaker()
    s.generate_audio(Message=msg, TextType='text',
                     VoiceId=voice)
    s.speak(IncludeChime=include_chime)


@click.group()
@click.option('--profile', default='pollexy')
@click.option('--region')
def cli(profile, region):
    print 'profile = {}'.format(profile)
    os.environ['AWS_PROFILE'] = profile
    if region:
        print 'region = {}'.format(region)
        os.environ['AWS_DEFAULT_REGION'] = region
    pass


def error_if_missing(obj, param):
    if not hasattr(obj, param) or (hasattr(obj, param) and
                                   not getattr(obj, param)):
        raise ValueError("Missing --%s" % param)


def missing_or_empty(obj, param):
    if not hasattr(obj, param) or (hasattr(obj, param) and
                                   not getattr(obj, param)):
        return True
    else:
        return False


def error_if_all(obj, items):
    i = 0
    for item in items:
        if not missing_or_empty(obj, item):
            i += 1
    if (len(items) == i):
        raise ValueError("Can't pass these items at the same time: %s"
                         % ",".join(items))


@cli.group('lex')
def lex():
    pass


@lex.group('bot')
def lex_bot():
    pass


@lex_bot.command('apply')
@click.argument('config_path')
def apply_bots(config_path):
    bm = LexBotManager(ConfigPath=config_path)
    bots = bm.load_bots()
    for k in bots.keys():
        bot = bots[k]
        status, bot = bm.upsert(bot)
        if not status == 'FAILED':
            bot = bm.create_version(bot)
            bot = bm.update_alias(bot, Version='$LATEST')


@lex_bot.command('delete')
@click.argument('bot_name')
def delete_botbot_name(bot_name):
    bm = LexBotManager()
    bm.delete_bot(Name=bot_name)


@lex.group('intent')
def lex_intent():
    pass


@lex.group('slot_type')
def lex_slot_type():
    pass


@lex_slot_type.command('apply')
@click.argument('config_path')
def apply_slots(config_path):
    sm = LexSlotManager(ConfigPath=config_path)
    slots = sm.load()
    for i in slots.keys():
        slot = slots[i]
        print slot
        slot = sm.upsert(slot)


@lex_intent.command('apply')
@click.argument('config_path')
def apply_intents(config_path):
    im = LexIntentManager(ConfigPath=config_path)
    intents = im.load()
    for i in intents.keys():
        intent = intents[i]
        intent = im.upsert(intent)
        im.create_version(intent)


@lex.command('play')
@click.argument('bot_names')
@click.option('--alias', default='LATEST')
@click.option('--username', default='PollexyUser')
@click.option('--no_audio/--audio', default=False)
def lex_play(bot_names, alias, username, no_audio):
    lp = LexPlayer(
        BotNames=bot_names,
        Alias=alias,
        Username=username,
        NoAudio=no_audio)
    while (not lp.is_done):
        lp.get_user_input()


@cli.group('person')
def person():
    pass


@person.command('upsert')
@click.argument('name')
@click.option('--req_phys_confirmation', is_flag=True)
@click.option('--no_phys_confirmation', is_flag=True)
@click.option('--location_windows', required=False)
def person_update(name, req_phys_confirmation, no_phys_confirmation,
                  location_windows):
    pm = PersonManager()

    if req_phys_confirmation:
        req_phys = True

    elif no_phys_confirmation:
        req_phys = False

    else:
        req_phys = None

    pm.update_person(
        Name=name,
        RequirePhysicalConfirmation=req_phys,
        Windows=location_windows)


@person.command('list')
def person_list():
    pm = PersonManager()
    people = pm.get_all()
    if people is None:
        click.echo("There are no people in the system")
    else:
        for p in people:
            click.echo('{} (req_phys={})'
                       .format(p.name,
                               p.require_physical_confirmation))
            for tw in json.loads(p.time_windows.to_json()):
                print '--{}\n{}'.format(tw['location_name'], tw['ical'])


@person.command('show')
@click.argument('name')
def person_show(name):
    pm = PersonManager()
    p = pm.get_person(name)
    if person is None:
        click.echo("{} does not exist in the system".format(name))
    else:
        click.echo('{} (req_phys={})'
                   .format(p.name,
                           p.require_physical_confirmation))


@cli.group('location')
def location():
    pass


@location.command('create')
@click.argument('name')
def location_create(name):
    lm = LocationManager()
    lm.create(Name=name)


@location.command('list')
def location_list():
    lm = LocationManager()
    locs = lm.get_all()
    if locs is None:
        click.echo("There are no locations")
    else:
        for l in locs:
            click.echo(l.location_name)


@cli.group('message')
def message():
    pass


@message.command('list')
@click.argument('person_name')
@click.option('--include_expired/--dont_include_expired', default=False)
def list(person_name, include_expired):
    s = Scheduler()
    msgs = s.get_messages()
    for m in msgs:
        if not m.person_name == person_name:
            continue
        print '* {}\n "{}"\n Next: {}\n'.format(m.uuid_key,
                                                m.body,
                                                m.next_occurrence_local)


@message.command('speak')
@click.argument('person_name')
@click.argument('location_name')
@click.option('--ignore_confirmation/--dont_ignore_confirmation',
              default=False)
@click.option('--no_audio/--audio', default=False)
@click.option('--ignore_motion/--dont_ignore_motion', default=True)
@click.option('--simulate/--dont_simulate', default=False)
@click.option('--voice_id')
@click.option('--fail_confirm/--dont_fail_confirm', default=False)
def speak(person_name,
          location_name,
          ignore_motion,
          ignore_confirmation,
          voice_id,
          no_audio,
          simulate,
          fail_confirm):
    try:
        while True:
            click.echo("Checking for messages . . .")

            lm = LocationManager()
            loc = lm.get_location(location_name)
            if not ignore_motion and not loc.is_motion:
                print 'Exiting. No motion detected at ' + location_name
                exit(1)
            speaker = Speaker(NoAudio=no_audio)
            message_manager = MessageManager(LocationName=location_name)
            click.echo('getting files')
            cache_manager = CacheManager(BucketName='pollexy-media',
                                         CacheName='chimes')
            cache_manager.sync_remote_folder()
            print 'Writing speech'
            vid, speech = message_manager.write_speech(PersonName=person_name)
            if vid:
                voice_id = vid
            if not speech:
                print "I have nothing to say"
                message_manager.delete_sqs_msgs()
            else:
                print "Speech:\n\n%s" % speech
                try:
                    pm = PersonManager()
                    p = pm.get_person(person_name)
                    do_speech = True
                    if fail_confirm:
                        logging.warning("FORCE FAILING confirmation")
                        reason, do_speech = "NoResponse", False

                    elif not no_audio and p.require_physical_confirmation and \
                            not ignore_confirmation:
                        lv = LocationVerification(PersonName=person_name,
                                                  LocationName=location_name,
                                                  VoiceId=voice_id)
                        do_speech, retry_count, timeout = \
                            lv.verify_person_at_location(SpeechMethod=say)

                    if do_speech:
                        speaker = Speaker(NoAudio=no_audio)
                        speaker.generate_audio(Message=speech, TextType='ssml',
                                               VoiceId=voice_id)
                        speaker.speak(IncludeChime=True)
                        message_manager.succeed_speech(dont_delete=simulate)
                    else:
                        message_manager.fail_speech(Reason=reason)
                finally:
                    speaker.cleanup()

    except Exception as exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print repr(traceback.format_exception(exc_type, exc_value,
                   exc_traceback))
        click.echo("Error: %s" % str(exc))
        exit(2)


@message.command('queue')
@click.option('--simulate/--dont_simulate')
@click.option('--simulated_date')
def queue(simulate, simulated_date):
    try:
        if simulated_date:
            dt = arrow.get(simulated_date)
        else:
            dt = arrow.utcnow()
        scheduler = Scheduler()
        print 'getting messages'
        msgs = scheduler.get_messages()
        logging.info("Starting MessageManager")
        logging.info("messages = %s" % len(msgs))
        if len(msgs) == 0:
            click.echo("No messages are ready to be queued")
        else:
            click.echo("Number of messages to be scheduled: %s" % len(msgs))
        for m in msgs:
            if not simulate:
                logging.info("Getting person %s " % m.person_name)
                pm = PersonManager()
                p = pm.get_person(m.person_name)
                if not p:
                    logging.warn(m.person_name +
                                 "does not have an entry in the " +
                                 "Person table")
                    continue
                if p.all_available_count(dt) == 0:
                    logging.warn('No locations available for %s' %
                                 m.person_name)
                    click.echo('No locations available for %s' %
                               m.person_name)
                    continue
                avail_windows = p.all_available(dt)
                click.echo('# of locations avail: {}, last_loc={}'
                           .format(p.all_available_count(dt),
                                   m.last_loc))
                if m.last_loc == p.all_available_count(dt)-1:
                    click.echo('Resetting to first location')
                    idx = 0
                else:
                    click.echo('Moving to next location')
                    idx = m.last_loc + 1

                active_window = avail_windows[int(idx)]
                next_exp = m.next_expiration_utc.isoformat()
                mm = MessageManager(LocationName=active_window.location_name)
                click.echo("Publishing message for person %s to location %s"
                           % (m.person_name, active_window.location_name))
                mm.publish_message(Body=m.body, UUID=m.uuid_key,
                                   PersonName=m.person_name,
                                   NoMoreOccurrences=m.no_more_occurrences,
                                   ExpirationDateTimeInUtc=next_exp)
                scheduler.update_queue_status(m.uuid_key, m.person_name, True)
                scheduler.update_last_location(m.uuid_key, m.person_name, idx)
            else:
                click.echo("Publishing message(simulated):")
                click.echo(str(m))

    except Exception:
        print 'here'
        click.echo(traceback.print_exc())
        raise


@message.command('schedule')
@click.argument('person_name')
@click.argument('message')
@click.option('--expiration_datetime')
@click.option('--ical')
@click.option('--start_datetime')
@click.option('--frequency')
@click.option('--interval')
@click.option('--count')
@click.option('--lexbot')
@click.option('--timezone')
def message_schedule(person_name,
                     message,
                     expiration_datetime,
                     ical,
                     count,
                     frequency,
                     lexbot,
                     interval,
                     timezone,
                     start_datetime):
    try:
        click.echo("Scheduling message for person {}".format(person_name))
        scheduler = Scheduler()
        if start_datetime is None:
            click.echo("Setting start time to now")
            start_datetime = arrow.utcnow()
        else:
            start_datetime = arrow.get(start_datetime)
            click.echo("Setting custom start time to %s" % start_datetime)

        if expiration_datetime is None:
            expiration_datetime = start_datetime.replace(years=1000)
        else:
            expiration_datetime = arrow.get(expiration_datetime)

        message = ScheduledMessage(
            StartDateTimeInUtc=start_datetime,
            ical=ical,
            Body=message,
            PersonName=person_name,
            Frequency=frequency,
            Count=count,
            Lexbot=lexbot,
            TimeZone=timezone,
            Interval=interval,
            EndDateTimeInUtc=expiration_datetime)
        scheduler.schedule_message(message)

    except Exception:
        click.echo(traceback.print_exc())
        exit(2)


def print_simulation_mode(obj):
    if (obj.simulate):
        click.echo("*SIMULATION ONLY*")


@message.command('teach')
@click.option('--no_audio/--audio', default=False)
@click.option('--voice_id', default="Joanna")
def teach(no_audio, voice_id):
    try:
        c = ConfigHelper().config
        cache_manager = CacheManager(BucketName='pollexy-media',
                                     CacheName='chimes')
        cache_manager.sync_remote_folder()
        chime = c['teach_chime']
        speech = random.choice(c['teach_phrases'])
        speaker = Speaker(NoAudio=no_audio)
        logging.info('Teach phrase={}'.format(speech))
        speaker.generate_audio(Message=speech, TextType='text',
                               VoiceId=voice_id)
        speaker.speak(IncludeChime=True, Chime=chime)
        speaker.cleanup()

    except Exception as exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print repr(traceback.format_exception(exc_type, exc_value,
                   exc_traceback))
        click.echo("Error: %s" % str(exc))
        exit(2)


@message.command('say')
@click.argument('person_name')
@click.argument('location_name')
@click.argument('message')
@click.argument('--voice_id', default="Joanna")
def message_say(person_name, location_name, message, voice_id):
    try:
        lv = LocationVerification(PersonName=person_name,
                                  LocationName=location_name,
                                  VoiceId=voice_id)
        done, retry_count, timeout = \
            lv.verify_person_at_location(SpeechMethod=say)

        if done:
            say(Message=message, VoiceId=voice_id)
        else:
            print "Can't verify {} at location".format(person_name)

    except Exception as exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print repr(traceback.format_exception(exc_type, exc_value,
                   exc_traceback))
        click.echo("Error: %s" % str(exc))
        exit(2)


@cli.command()
@click.pass_obj
def upload_face(obj):
    try:
        error_if_missing(obj, 'person')
        error_if_missing(obj, 'path')
        error_if_missing(obj, 'collection')
        person = obj.person
        path = obj.path
        collection = obj.collection
        fm = FaceManager(Bucket='face-db-pollexy')
        fm.upload_face(Path=path, Person=person, Collection=collection)
    except Exception as exc:
        click.echo("Error: %s" % str(exc))
        exit(2)


@cli.command()
@click.pass_obj
def match_face(obj):
    try:
        error_if_missing(obj, 'path')
        error_if_missing(obj, 'collection')
        path = obj.path
        collection = obj.collection
        fm = FaceManager(Bucket='face-db-pollexy')
        response = fm.match_face(Path=path, Collection=collection)
        print response
    except Exception as exc:
        click.echo("Error: %s" % str(exc))
        exit(2)


@cli.command()
@click.pass_obj
def update_location_activity(obj):
    try:
        error_if_missing(obj, 'location_name')
        location_name = obj.location_name
        lm = LocationManager()
        response = lm.update_location_activity(location_name)
        print response
    except Exception as exc:
        click.echo("Error: %s" % str(exc))
        exit(2)


@cli.command()
@click.pass_obj
def update_library_message(obj):
    try:
        error_if_missing(obj, 'message_name')
        error_if_missing(obj, 'message')
        lm = LibraryManager()
        lm.update_message(Name=obj.message_name, Message=obj.message)
    except Exception as exc:
        click.echo("Error: %s" % str(exc))


@cli.group('serverless')
def srvls():
    pass


@srvls.command('deploy')
def deploy():
    call(["serverless", "deploy"])


@cli.group('terraform')
def tf():
    pass


@tf.command()
def plan():
    tf = Terraform(working_dir='./terraform')
    parser = SafeConfigParser()
    config = os.path.expanduser('~/.aws/config')
    parser.read(config)
    if not parser.has_section('profile pollexy'):
        print "You need to run 'pollexy credentials configure'"
        return
    region = parser.get('profile pollexy', 'region')
    print 'Initializing environment . . . ' + region
    code, stdout, stderr = tf.init()
    print stderr
    print stdout

    print 'Planning environment . . . '
    code, stdout, stderr = tf.plan(var={'aws_region': region})
    if (stderr):
        print stderr
    else:
        print stdout


@tf.command()
def apply():
    tf = Terraform(working_dir='./terraform')
    parser = SafeConfigParser()
    config = os.path.expanduser('~/.aws/config')
    parser.read(config)
    if not parser.has_section('profile pollexy'):
        print "You need to run 'pollexy credentials configure'"
        return
    region = parser.get('profile pollexy', 'region')
    print 'Applying environment . . . '
    code, stdout, stderr = tf.apply(var={'aws_region': region})
    if (stderr):
        print stderr
    else:
        print stdout


@tf.command()
def destroy():
    tf = Terraform(working_dir='./terraform')
    parser = SafeConfigParser()
    parser = SafeConfigParser()
    config = os.path.expanduser('~/.aws/config')
    parser.read(config)
    if not parser.has_section('profile pollexy'):
        print "You need to run 'pollexy credentials configure'"
        return
    region = parser.get('profile pollexy', 'region')
    print 'Destroying environment . . . '
    code, stdout, stderr = tf.destroy(var={'aws_region': region})
    if (stderr):
        print stderr
    else:
        print stdout


@cli.group('credentials')
def creds():
    pass


@creds.command()
@click.argument('access_key')
@click.argument('secret_key')
@click.argument('region')
def configure(access_key, secret_key, region):
    aws_folder = os.path.expanduser('~/.aws')
    if not os.path.isdir(aws_folder):
        os.makedirs(aws_folder)
    config_parser = SafeConfigParser()
    creds_parser = SafeConfigParser()
    config = os.path.expanduser('~/.aws/config')
    creds = os.path.expanduser('~/.aws/credentials')
    creds_parser.read(creds)
    config_parser.read(config)
    config_sect = 'profile pollexy'
    creds_sect = 'pollexy'
    if config_sect not in config_parser.sections():
        config_parser.add_section(config_sect)
    if creds_sect not in creds_parser.sections():
        creds_parser.add_section(creds_sect)
    creds_parser.set(creds_sect, 'aws_access_key_id', access_key)
    creds_parser.set(creds_sect, 'aws_secret_access_key', secret_key)
    config_parser.set(config_sect, 'region', region)
    with open(config, 'w') as config_file:
        config_parser.write(config_file)
    with open(creds, 'w') as creds_file:
        creds_parser.write(creds_file)


if __name__ == '__main__':
    cli(obj=Config())


def click_warn(msg):
    logging.warn(msg)
    click.echo(msg)
