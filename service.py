import base64
import logging
import constant
import boto3
from botocore.exceptions import ClientError

ec2_client = boto3.client("ec2", region_name=constant.REGION_NAME)
ec2_resources = boto3.resource("ec2", region_name=constant.REGION_NAME)
sqs_client = boto3.client('sqs', region_name=constant.REGION_NAME)
sqs_resources = boto3.resource('sqs', region_name=constant.REGION_NAME)
s3_client = boto3.client('s3', region_name=constant.REGION_NAME)
s3_resources = boto3.resource('s3', region_name=constant.REGION_NAME)

response_dict = {}

async def send_request(filename, stream):
    try:
        encoded_img = base64.b64encode(stream.read())
        encoded_img = encoded_img.decode('utf-8')
        sqs_client.send_message(QueueUrl=constant.REQUEST_QUEUE_URL,
                                MessageBody=filename,
                                MessageAttributes={'encoded_img': {'StringValue':encoded_img, 'DataType':'String'}})
    except ClientError as e:
        logging.error(e)
        return False

    output = await fetch_result(filename.split(".")[0])
    return output

async def fetch_result(img):
    output = None
    while output is None:
        # loop through queue until no more messages left
        while int(get_num_messages_in_queue(constant.RESPONSE_QUEUE_URL)) > 0:
            if img in response_dict.keys():
                return response_dict[img]

            response = sqs_client.receive_message(QueueUrl=constant.RESPONSE_QUEUE_URL,
                                                  MaxNumberOfMessages=10,
                                                  MessageAttributeNames=['All']
                                                  )

            messages = response.get('Messages', [])
            for message in messages:
                receipt_handle = message['ReceiptHandle']
                result = message['Body']
                resp_img = message['MessageAttributes']['img']['StringValue']  # getting img
                response_dict[resp_img] = result
                sqs_client.delete_message(QueueUrl=constant.RESPONSE_QUEUE_URL, ReceiptHandle=receipt_handle)
                print('Message deleted.')

            if img in response_dict.keys():
                return response_dict[img]

    return output

def clear_buckets():
    response_dict.clear()
    bucket = s3_resources.Bucket(constant.INPUT_BUCKET_NAME)
    bucket.object_versions.delete()

    bucket = s3_resources.Bucket(constant.OUTPUT_BUCKET_NAME)
    bucket.object_versions.delete()

# Clears SQS  queue
def clear_queue():
    response_queue = sqs_resources.Queue(url=constant.RESPONSE_QUEUE_URL)
    request_queue = sqs_resources.Queue(url=constant.REQUEST_QUEUE_URL)
    try:
        response_queue.purge()
        request_queue.purge()
    except:
        pass



def get_num_messages_in_queue(queue_url):
    response = sqs_client.get_queue_attributes(QueueUrl = queue_url, AttributeNames = ['ApproximateNumberOfMessages'])
    return response['Attributes']['ApproximateNumberOfMessages']