const APIKEY = "no4fxQ62w67DPHUGsSVWm7UrTtEGOnbB68Vi9NfT";
const REGION = 'us-east-1'



// Function to upload images to S3 bucket
// ---------------------------------------------------------------------------------------
function uploadToS3(e) {
    e.preventDefault();
    console.log("Uploading to S3 Bucket");

    let fileInfo = $('#upload-photo-form')[0].files[0];
    let filenameInput = fileInfo.name;
    // Format filename (remove spaces)
    let filename = filenameInput.replace(/\s/g, '');
    console.log("Filename", filename)
    let customLabels = $('#custom-labels').val();
    console.log("CUSTOM LABELS-->", customLabels)

    // Uploading to S3 bucket via API /PUT method
    async function uploadphotoPUT() {
        e.preventDefault();
        console.log("Upload button clicked...");

        // Connect to API Gateway
        let apigClient = apigClientFactory.newClient({apiKey: APIKEY});
        console.log("apigClient", apigClient);

        // base64 encode the image
        let result = await getBase64(fileInfo);
        result = result.replace(/^data:image\/(png|jpg|jpeg);base64,/,"");
        // console.log("RESULT:", result);

        let params = {
            "bucket": "b2-photo-storage",
            "key": filename,
            "Content-Type": fileInfo.type,
            "Content-Encoding": "base64", // Add this to prevent 415 error
            'x-amz-meta-customLabels': customLabels, // Add custom labels here *
        };
        let body = result;
        let additionalParams = {};

        // API GATEWAY
        apigClient.uploadBucketKeyPut(params, body, additionalParams);
    }

    uploadphotoPUT()
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
    let searchquery = $('#transcript').val();
    console.log("SEARCH QUERY: ", searchquery);

    var params = {q: searchquery};
    var body = {};
    var additionalParams = {};

    searchAPI(params, body, additionalParams);
}


// Search using API /GET method
async function searchAPI(params, body, additionalParams){

    // Connect to API Gateway
    let apigClient = apigClientFactory.newClient({apiKey: APIKEY});
    console.log("apigClient", apigClient);

    try {
        // API GATEWAY
        const getresponse = await apigClient.searchGet(params, body, additionalParams);

        if (getresponse) {
            let pictures = getresponse.data;
            if (pictures.length === 0){
                let pNode = document.createElement('P');
                let textnode = document.createTextNode("No images found.");
                pNode.append(textnode);
                document.getElementById("photo-grid").appendChild(pNode);
                return
            }

            // Render images
            for (i=0; i<pictures.length; i++){
                let pic = document.createElement('img');
                pic.src = "https://s3.amazonaws.com/b2-photo-storage/" + pictures[i];
                pic.style.margin = "3px";
                pic.style.height = "200px";
                document.getElementById("photo-grid").appendChild(pic);
            }
        }
    } catch (error){
        console.log("Error", error);
    }
}
