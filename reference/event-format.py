# Format of event Records object after user uploads photo into S3 bucket (for testing index-photos lambda)
{"Records":
    [
        {
            "eventVersion": "2.1",
            "eventSource": "aws:s3",
            "awsRegion": "us-east-1",
            "eventTime": "2021-03-18T01:04:53.933Z",
            "eventName": "ObjectCreated:Put",
            "userIdentity": {"principalId": "12345"},
            "requestParameters": {"sourceIPAddress": "100.8.000.00"},
            "responseElements": {"x-amz-request-id": "123456", "x-amz-id-2": "123456/abcdefg"},
            "s3":{
                "s3SchemaVersion": "1.0",
                "configurationId": "upload-photo",
                "bucket": {"name": "b2-photo-storage", "ownerIdentity": {"principalId": "123456"}, "arn": "arn:aws:s3:::b2-photo-storage"},
                "object": {
                    "key": "icecream.png", "size": 202177, "eTag": "123456789", "versionId": "123456789.0Z", "sequencer": "123456"
                }
            }
        }
    ]
}
