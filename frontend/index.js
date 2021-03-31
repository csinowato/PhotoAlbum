const APIKEY = "no4fxQ62w67DPHUGsSVWm7UrTtEGOnbB68Vi9NfT";
const REGION = 'us-east-1'



// Function to upload images to S3 bucket
// ---------------------------------------------------------------------------------------
function uploadToS3(e) {
    e.preventDefault()
    console.log("Uploading to S3 Bucket")

    let fileInfo = $('#upload-photo-form')[0].files[0]
    let filename = fileInfo.name
    let customLabels = $('#custom-labels').val()
    console.log("CUSTOM LABELS-->", customLabels)

    // Uploading to S3 bucket via API /PUT method
    async function uploadphotoPUT() {
        e.preventDefault()
        console.log("Upload button clicked...")

        // Connect to API Gateway
        let apigClient = apigClientFactory.newClient({apiKey: APIKEY})
        console.log("apigClient", apigClient)

        // base64 encode the image
        let result = await getBase64(fileInfo)
        result = result.replace(/^data:image\/(png|jpg|jpeg);base64,/,"")
        console.log("RESULT:", result)

        let params = {
            "bucket": "b2-photo-storage",
            "key": filename,
            "Content-Type": fileInfo.type,
            "Content-Encoding": "base64", // Add this to prevent 415 error
            'x-amz-meta-customLabels': customLabels, //ADD CUSTOM LABELS HERE
        };
        let body = result
        let additionalParams = {}

        // API GATEWAY
        apigClient.uploadBucketKeyPut(params, body, additionalParams)
    }

    uploadphotoPUT()



    // Testing -- Uploading to S3 bucket directly

    // async function directupload() {

    //     AWS.config.update({
    //         accessKeyId: ACCESSKEYID,
    //         secretAccessKey: SECRETACCESSKEY,
    //     });

    //     let s3 = new AWS.S3();

    //     let params = {
    //         Bucket: "b2-photo-storage",
    //         Key: filename,
    //         Body: fileInfo,
    //         ContentEncoding: 'base64',
    //         ContentType: fileInfo.type, //'image/png'
    //         Metadata: {
    //             //if directly updating, x-amz-meta prefix gets added automatically
    //             'customLabels': customLabels
    //         },
    //         ACL:'public-read'
    //     };

    //     s3.putObject(params, function(err, data) {
    //         if (err) console.log(err, err.stack);
    //         else console.log(data);
    //     });
    // }

    // directupload()
    // https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/S3.html#putObject-property
};


// Convert Image to Base 64
function getBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}
// https://stackoverflow.com/questions/36280818/how-to-convert-file-to-base64-in-javascript




// Function to search for images
// ---------------------------------------------------------------------------------------
function searchforphotos(e) {
    e.preventDefault()

    // Clear previous search results
    let node = document.getElementById("photo-grid");
    node.innerHTML = '';

    // Get user's input
    let searchquery = $('#transcript').val()
    console.log("SEARCH QUERY: ", searchquery)

    var params = {q: searchquery};
    var body = {};
    var additionalParams = {}

    searchAPI(params, body, additionalParams)
}


// Search using API /GET method
async function searchAPI(params, body, additionalParams){

    // Connect to API Gateway
    let apigClient = apigClientFactory.newClient({apiKey: APIKEY})
    console.log("apigClient", apigClient)

    try {
        // API GATEWAY
        const getresponse = await apigClient.searchGet(params, body, additionalParams)

        if (getresponse) {
            let pictures = getresponse.data
            if (pictures.length === 0){
                console.log("NO IMAGES") //show on frontend later
                return
            }

            // Render images
            for (i=0; i<pictures.length; i++){
                pic = document.createElement('img')
                pic.src = "https://s3.amazonaws.com/b2-photo-storage/" + pictures[i]
                pic.style.margin = "3px"
                pic.style.height = "200px"
                document.getElementById("photo-grid").appendChild(pic);
            }
        }
    } catch (error){
        console.log("Error", error)
    }
}
