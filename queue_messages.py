from messages.message_manager import MessageManager
from scheduler.scheduler import Scheduler
from person.person import PersonManager
import arrow
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    scheduler = Scheduler()
    dt = arrow.utcnow()
    logging.info("Getting messages")
    msgs = scheduler.get_messages()
    logging.info("messages = %s" % len(msgs))
    if len(msgs) == 0:
        logging.info("No messages are ready to be queued")
    else:
        logging.info("Number of messages to be scheduled: %s" % len(msgs))

    for m in msgs:
        logging.info("Getting person %s " % m.person_name)
        pm = PersonManager()
        p = pm.get_person(m.person_name)
        if not p:
            logging.warn(m.person_name +
                         "does not have an entry in the " +
                         "Person table . . . skipping")
            continue
        if p.all_available_count(dt) == 0:
            logging.warn('No locations available for %s . . . skipping' %
                         m.person_name)
            continue
        avail_windows = p.all_available(dt)
        logging.info('# of locations avail: {}, last_loc={}'
                     .format(p.all_available_count(dt),
                             m.last_loc))
        if p.all_available_count(dt) > 1 and \
                m.last_loc == p.all_available_count(dt)-1:
            logging.info('Resetting to first location')
            idx = 0
        else:
            if p.all_available_count(dt) > 1:
                logging.info('Moving to next location')
                idx = m.last_loc + 1
            else:
                idx = 0

            active_window = avail_windows[int(idx)]
            next_exp = m.next_expiration_utc.isoformat()
            mm = MessageManager(LocationName=active_window.location_name)
            logging.info("Publishing message for person %s to location %s"
                         % (m.person_name, active_window.location_name))
            mm.publish_message(Body=m.body, UUID=m.uuid_key,
                               PersonName=m.person_name,
                               NoMoreOccurrences=m.no_more_occurrences,
                               BotNames=m.bot_names,
                               IceBreaker=m.ice_breaker,
                               RequiredBots=m.required_bots,
                               ExpirationDateTimeInUtc=next_exp)
            scheduler.update_queue_status(m.uuid_key, m.person_name, True)
            scheduler.update_last_location(m.uuid_key, m.person_name, idx)
