import time
import boto3
import uuid
import constant
from instances import Instances as instances
from botocore.exceptions import ClientError

ec2_client = boto3.client("ec2", region_name=constant.REGION_NAME)
# ec2_resources = boto3.resource("ec2", region_name=constant.REGION_NAME)
sqs_client = boto3.client('sqs', region_name=constant.REGION_NAME)

stopped_instances = []
running_instances = []
pending_instances = []
stopping_instances = []

def create_or_start_ec2_instance(req_instances):
    count = 19 - len(running_instances) - len(stopped_instances) - len(pending_instances) - len(stopping_instances)
    req_instances -= len(pending_instances)
    print("req_instances to be start", req_instances)
    print("instance rem", count)
    ins = []
    for i in range(0, min(req_instances, len(stopped_instances))):
        ins.append(stopped_instances[i].instance_id)
        req_instances -= 1

    if ins:
        ec2_client.start_instances(InstanceIds=ins)

    if(count <= 0):
        return

    for i in range(0, min(count, req_instances)):
        try:
            ec2_client.run_instances(
                ImageId=constant.AMI_IMAGE,
                MinCount=1,
                MaxCount=1,
                InstanceType="t2.micro",
                KeyName="Assignment1",
                SecurityGroupIds=[
                    'sg-0daa75347318483dd'  # Project 1 EC2 Security Group ID
                ],
                TagSpecifications=[{  # Give instance name based on App Tier ID
                    'ResourceType': 'instance',
                    'Tags': [{
                        'Key': 'Name',
                        'Value': f'app-instance-{uuid.uuid4()}'
                    }]
                }]
            )
        except ClientError as e:
            print(e)

    print("EC2 instances started")


def stop_ec2_instance(req_instances):
    ins = []
    for i in range(0, req_instances):
        ins.append(running_instances[i].instance_id)

    ec2_client.stop_instances(InstanceIds=ins)
    print("EC2 instances stopped")

while True:
    response = sqs_client.get_queue_attributes(
        QueueUrl=constant.REQUEST_QUEUE_URL,
        AttributeNames=[
            'ApproximateNumberOfMessages',
            'ApproximateNumberOfMessagesNotVisible'
        ]
    )
    stopped_instances.clear()
    running_instances.clear()
    pending_instances.clear()
    stopping_instances.clear()

    num_visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    num_invisible_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
    num_requests = num_visible_messages + num_invisible_messages
    print("number of visible request = ", num_visible_messages)
    print("number of invisible request = ", num_invisible_messages)


    instances_details = ec2_client.describe_instances()

    for instance in instances_details['Reservations']:
        for instance_detail in instance['Instances']:
            #print(instance_detail['Tags'][0]['Value'])
            if (instance_detail['Tags'][0]['Value'] != 'Web-Tier'):
                if (instance_detail['State']['Name'] == 'running'):
                    running_instances.append(instances(instance_detail['InstanceId'], instance_detail['State']['Name']))
                elif((instance_detail['State']['Name'] == 'stopped')):
                    stopped_instances.append(instances(instance_detail['InstanceId'], instance_detail['State']['Name']))
                elif(instance_detail['State']['Name'] == 'stopping'):
                    stopping_instances.append(instances(instance_detail['InstanceId'], instance_detail['State']['Name']))
                elif (instance_detail['State']['Name'] == 'pending'):
                    pending_instances.append(instances(instance_detail['InstanceId'], instance_detail['State']['Name']))

    req_instances = num_requests - len(running_instances)

    print("pending = ", len(pending_instances))
    print("running = ", len(running_instances))
    print("Req_instance = ", req_instances)
    if req_instances >=0:
        create_or_start_ec2_instance(req_instances)
    else:
        stop_ec2_instance(abs(req_instances))

    time.sleep(10)


