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


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    text = event['queryStringParameters']['q']
    print('TEXT', text)

    # Call Lex Chatbot
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='PhotoAlbumBot',
        botAlias='prod',
        userId='user',
        inputText=text #send user input to lex chatbot
    )

    print("RESPONSE FROM LEX", response)


    # logger.debug('event.bot.name={}'.format(event['bot']['name']))
    # return dispatch(event)

    first_label = response['slots']['firstlabel']
    second_label = response['slots']['secondlabel']

    print("FIRST LABEL", first_label)
    print("SECOND LABEL", second_label)


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

    # Search for first label
    searchresults = []
    search_res = es.search(index="photos", body={"query": {"match": {'labels': first_label}}})
    for hit in search_res['hits']['hits']:
        searchresults.append(hit['_source']['objectKey'])

    # Search for second label if any
    if second_label:
        search_res2 = es.search(index="photos", body={"query": {"match": {'labels': second_label}}})
        for hit in search_res2['hits']['hits']:
            searchresults.append(hit['_source']['objectKey'])
    # https://elasticsearch-py.readthedocs.io/en/v7.11.0/

    print('SEARCH RESULTS', searchresults)

    # Remove duplicate files
    unique_results = list(set(searchresults))
    print("UNIQUE -->", unique_results)


    return {
        "statusCode": 200,
        'headers': {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(unique_results)
        # "isBase64Encoded": true|false,
    }


