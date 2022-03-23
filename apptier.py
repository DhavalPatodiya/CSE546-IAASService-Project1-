import os
import time
import boto3
import base64
import json
import io

sqs_client = boto3.client('sqs', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')

sqs_request_url = 'https://sqs.us-east-1.amazonaws.com/633040128103/RequestQueue'
sqs_response_url = 'https://sqs.us-east-1.amazonaws.com/633040128103/ResponseQueue'

input_bucket_name = 'cse546project.input.bucket'
output_bucket_name = 'cse546project.output.bucket'

def upload_image_to_s3(image_name, stream):
    s3_client.upload_fileobj(stream, input_bucket_name, image_name)

def upload_result_to_s3(image_name, result):
    s3_client.put_object(Key=image_name, Bucket=output_bucket_name, Body=result)

def download_image_to_instance(image_name):
    s3_client.download_file(input_bucket_name, image_name, image_name)

def classify_image(image_name):
    stdout = os.popen('python3 face_recognition.py ' + image_name)
    result = stdout.read().strip()
    return result

#Polling SQS queue
while True:
    # Dequeue a message from request queue
    response = sqs_client.receive_message(QueueUrl= sqs_request_url,
                                   MaxNumberOfMessages=1,
                                   MessageAttributeNames=['All']
                                   )

    messages = response.get('Messages', [])

    for message in messages:
        receipt_handle = message['ReceiptHandle']  # Needed for message deletion
        image_name = message['Body'] #image name is in Body
        img = message['MessageAttributes']['encoded_img']['StringValue'] #getting image

        #decoding img
        stream = (base64.b64decode(img))
        stream = io.BytesIO(stream)

        # Upload img to S3
        upload_image_to_s3(image_name, stream)

        #downloading img in Instance
        download_image_to_instance(image_name)

        # Do machine learning
        result = classify_image(image_name)
        print(result)

        # removing the image
        os.remove("/home/ec2-user/" + image_name)

        # Upload result to S3
        upload_result_to_s3(image_name.split(".")[0], result)

        # Sending message to Queue
        sqs_client.send_message(QueueUrl=sqs_response_url,
                                MessageBody=result,
                                MessageAttributes={'img': {'StringValue': image_name.split(".")[0], 'DataType': 'String'}}
                                )

        #deleting msg
        print('Deleting message...')
        sqs_client.delete_message(QueueUrl=sqs_request_url, ReceiptHandle=receipt_handle)
        print('Message deleted.')
        time.sleep(5)