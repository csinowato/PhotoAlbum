import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# ElasticSearch Instance
host = 'search-photos-cxixzknxphgyayje7oqyy63w7u.us-east-1.es.amazonaws.com'
region = 'us-east-1'



# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.
    Note that this function would have negative impact on performance.
    """
    try:
        return func()
    except KeyError:
        return None


# --- Functions to Validate Each Slot ---



# --- Functions to Validate Booking ---


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_search_picture(slots):
    first_label = try_ex(lambda: slots['firstLabel'])
    second_label = try_ex(lambda: slots['secondLabel'])

    # CURRENTLY NO VALIDATIONS -------------------------



""" --- Functions that control the bot's behavior --- """


def search_image(intent_request):
    """
    Performs dialog management and fulfillment for booking a car.
    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """
    slots = intent_request['currentIntent']['slots']
    first_label = try_ex(lambda: slots['firstLabel'])
    second_label = try_ex(lambda: slots['secondLabel'])


    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    # if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        # validation_result = validate_book_restaurant(intent_request['currentIntent']['slots']) # ------- no validation for now **************
        # if not validation_result['isValid']:
        #     slots[validation_result['violatedSlot']] = None
        #     return elicit_slot(
        #         session_attributes,
        #         intent_request['currentIntent']['name'],
        #         slots,
        #         validation_result['violatedSlot'],
        #         validation_result['message']
        #     )

        # return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # ElasticSearch auth
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    # Connect to ElasticSearch
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
    # https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-request-signing.html#es-request-signing-python

    # check
    checkdata = []
    res_check = es.search(index="photos", body={"query": {"match": {'labels': first_label}}}) ## ADD CHECK FOR SECOND LABEL
    for hit in res_check['hits']['hits']:
        checkdata.append(hit['_id'])

    print("RES", res_check)
    print('checkdata', checkdata)



    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': "You're all set. Have a good day."
        }
    )


# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'SearchIntent':
        return search_image(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
