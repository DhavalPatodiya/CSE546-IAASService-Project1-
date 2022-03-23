import os
import boto3
import service
import constant
from flask import Flask, request
from werkzeug.utils import secure_filename


# Flask Constructor
app = Flask(__name__)

sqs_client = boto3.client('sqs', region_name=constant.REGION_NAME)

@app.route("/")
def showHomePage():
    return "This is home page"

@app.route('/upload', methods=["POST"])
async def upload():
    if 'myfile' in request.files:
        img = request.files['myfile']
        filename = secure_filename(img.filename)
        # Secure the filename to prevent some kinds of attack

        if filename != '':
            file_ext = os.path.splitext(filename)[1]

            if(file_ext != ".jpg"):
                return "Image should be JPG"

            output = await service.send_request(img.filename, img.stream)

            print(output)
            return output
    else:
        return "Image is Missing!"

    return "Some Error Occurred"

@app.route('/reset', methods=['POST'])
def reset():
    service.clear_queue()
    service.clear_buckets()
    return { 'message': 'Successfully cleared S3 buckets and response queue!' }

# if __name__ == "__main__":
app.run(host='0.0.0.0', port=8080)