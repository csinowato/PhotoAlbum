// Uploading to S3 bucket directly - (for testing index-photos lambda before connecting to API Gateway)

async function directupload() {

    AWS.config.update({
        accessKeyId: ACCESSKEYID,
        secretAccessKey: SECRETACCESSKEY,
    });

    let s3 = new AWS.S3();

    let params = {
        Bucket: "b2-photo-storage",
        Key: filename,
        Body: fileInfo,
        ContentEncoding: 'base64',
        ContentType: fileInfo.type, //'image/png'
        Metadata: {
            //if directly updating, x-amz-meta prefix gets added automatically
            'customLabels': customLabels
        },
        ACL:'public-read'
    };

    s3.putObject(params, function(err, data) {
        if (err) console.log(err, err.stack);
        else console.log(data);
    });
}

directupload()
// https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/S3.html#putObject-property
