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

from messages.message_manager import LibraryManager, MessageManager
from person.person import PersonManager
import arrow
import logging


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Pollexy. How can I help you?"
    reprompt_text = "How can I help you?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using Pollexy."
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def queue_message(intent, session):

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    reprompt_text = 'Excuse me?'
    if 'person' in intent['slots'] and 'message' in intent['slots']:
        if 'voice' in intent['slots']:
            voice = str(intent['slots']['voice']['value'])
        else:
            voice = 'Joanna'
        person = str(intent['slots']['person']['value']).lower()
        name = intent['slots']['message']['value']
        dt = arrow.utcnow()
        pm = PersonManager()
        p = pm.get_person(person)
        lm = LibraryManager()
        m = lm.get_message(Name=name)
        if not p:
            logging.error('{} does not have an entry in the '
                          'Person table . . .'.format(person))
            speech_output = "Sorry, I don't know the name {}" \
                            .format(person)
            should_end_session = True

        elif not m:
            logging.error('There is no message named {}'.format(name))
            speech_output = "Sorry, I don't have a message named {}" \
                            .format(name)
            should_end_session = True

        elif p.all_available_count(dt) == 0:
            logging.error('No locations are available for {}'.format(person))
            speech_output = "Sorry, there are no locations for {}" \
                            .format(name)
            should_end_session = True

        else:
            active_window = p.all_available(dt)[0]
            mm = MessageManager(LocationName=active_window.location_name)
            speech_output = "Got it. Publishing message {} to {} at " \
                            "location {}".format(name,
                                                 person,
                                                 active_window.location_name)
            mm.publish_message(Body=m['message'],
                               PersonName=person,
                               Voice=voice)
            should_end_session = True
    else:
        logging.error('Missing person or message')
        speech_output = 'Person or message name is missing. Please try again'
        should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" +
          session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "QueueMessage":
        return queue_message(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or \
            intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
