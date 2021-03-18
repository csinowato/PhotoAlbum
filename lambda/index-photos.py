import json
import boto3
import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Key


BUCKET_NAME = "b2-photo-storage"

# ElasticSearch Instance
host = 'vpc-photos-cxixzknxphgyayje7oqyy63w7u.us-east-1.es.amazonaws.com/'
region = 'us-east-1'


def lambda_handler(event, context):
    print("EVENT", event)
    filename = event["Records"][0]['s3']['object']['key']
    print("FILENAME", filename)

    json_object = {
        "objectKey": filename,
        "bucket": BUCKET_NAME,
        "createdTimestamp": datetime.datetime.now().isoformat(),
        "labels": [
         ]
    }

    # Extract labels using Rekognition
    client=boto3.client('rekognition', 'us-east-1')
    response = client.detect_labels(Image={'S3Object':{'Bucket':BUCKET_NAME,'Name':filename}},
            MaxLabels=10, MinConfidence=80)
    for label in response['Labels']:
        json_object['labels'].append(label['Name'])
        print ("Label: " + label['Name'])
    # https://docs.aws.amazon.com/rekognition/latest/dg/labels-detect-labels-image.html


    s3client = boto3.client('s3')
    metadata = s3client.head_object(Bucket=BUCKET_NAME, Key=filename)
    print('metadata', metadata)
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html


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


    print('json', json_object)


    # Add to ElasticSearch
    res = es.index(index="photos", doc_type="Photo", id=filename, body=json.dumps(json_object))
    print("RESULT", res['result'])
    # https://elasticsearch-py.readthedocs.io/en/6.8.2/


    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
