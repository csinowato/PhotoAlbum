import json
import boto3
import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from boto3.dynamodb.conditions import Key
import base64

BUCKET_NAME = "b2-photo-storage"

# ElasticSearch Instance
host = 'search-photos-cxixzknxphgyayje7oqyy63w7u.us-east-1.es.amazonaws.com'
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

    s3 = boto3.resource('s3', region_name=region)
    obj = s3.Object(BUCKET_NAME, filename)
    img = obj.get()['Body'].read().decode('utf-8')
    img_body = img.split(',')[1] #the first part of the img file is the type i.e. image/jpeg so we only want the bytes part
    print("IMAGE FILE", img_body)

    # Rekognition requires images to be in base64 binary format, not just base64
    base64_binary = base64.b64decode(img_body)
    print("BINARY", base64_binary)

    # Extract labels using Rekognition
    client=boto3.client('rekognition', 'us-east-1')

    response = client.detect_labels(Image={'Bytes': base64_binary}, MinConfidence=80)
    print("REKOGNITION RESPONSE", response)
    # response = client.detect_labels(Image={'S3Object':{'Bucket':BUCKET_NAME,'Name':filename}},
            # MaxLabels=10, MinConfidence=80)
    for label in response['Labels']:
        json_object['labels'].append(label['Name'])
        print ("Label: " + label['Name'])
    # https://docs.aws.amazon.com/rekognition/latest/dg/labels-detect-labels-image.html


    # Extract custom labels and add them to json object
    s3client = boto3.client('s3')
    metadata = s3client.head_object(Bucket=BUCKET_NAME, Key=filename)
    customLabels = metadata['ResponseMetadata']['HTTPHeaders']['x-amz-meta-x-amz-meta-customlabels']
    customLabelsArr = [x.strip() for x in customLabels.split(',')]
    print('custom labels', customLabelsArr)
    for i in customLabelsArr:
        json_object['labels'].append(i)
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
    # Should ID be filename or just auto create - if using filename, files cant have the same name
    # res = es.index(index="photos", doc_type="Photo", id=filename, body=json.dumps(json_object))
    # Not including id parameter so elasticsearch can auto generate it (so different images can have the same filename)
    res = es.index(index="photos", doc_type="Photo", body=json.dumps(json_object))
    print("RESULT", res['result'])
    # https://elasticsearch-py.readthedocs.io/en/6.8.2/

    # check
    checkdata = []
    res_check = es.search(index="photos", body={"query": {"match": {'labels': 'Food'}}})
    for hit in res_check['hits']['hits']:
        checkdata.append(hit['_id'])

    print("RES", res_check)
    print('checkdata', checkdata)



    return {
        'statusCode': 200,
        # 'body': json.dumps('Hello from Lambda!')
    }
