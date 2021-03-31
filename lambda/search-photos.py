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

    # Handle invalid user searches
    if 'slots' not in response:
        return {
            "statusCode": 200,
            'headers': {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps([])
        }

    # Extract labels
    first_label = response['slots']['firstlabel']
    second_label = response['slots']['secondlabel']

    print("FIRST LABEL", first_label)
    print("SECOND LABEL", second_label)

    # Get singular versions of labels
    labels_to_check = [first_label]
    if first_label[-1] == 's':
        labels_to_check.append(first_label[:-1])
    if second_label:
        labels_to_check.append(second_label)
        if second_label[-1] == 's':
            labels_to_check.append(second_label[:-1])

    print("LABELS TO CHECK", labels_to_check)


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


    searchresults = []

    # Search function
    def elasticsearch_helper(labelname):
        search_res = es.search(index="photos", body={"query": {"match": {'labels': labelname}}})
        for hit in search_res['hits']['hits']:
            searchresults.append(hit['_source']['objectKey'])
    # https://elasticsearch-py.readthedocs.io/en/v7.11.0/

    # Call search function
    for i in labels_to_check:
        elasticsearch_helper(i)
    print('SEARCH RESULTS', searchresults)


    # Remove duplicate files
    unique_results = list(set(searchresults))
    print("UNIQUE RESULTS", unique_results)


    return {
        "statusCode": 200,
        'headers': {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(unique_results)
        # "isBase64Encoded": true|false,
    }


