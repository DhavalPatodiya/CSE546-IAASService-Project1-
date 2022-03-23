# CSE546-IAASService-Project1-


**Problem Statement**

In this rapidly changing world of computing, the scale of users changes from time to time. A company may have users who can use the application at a particular time of day. To satisfy the users, companies have to scale their resources like storage, processing, etc. The availability and consistency of the application should be high to meet the demanding scale of users. Investing in this large amount of resources may leave the company with a financial burden and it is time- consuming as well. That’s where cloud computing comes in. It’s the new paradigm where resources are offered as on-demand services. However, due to the cost, it is important to monitor the use of resources and avoid the exploitation of resources. The main aim of this project is to create a scalable cloud application that will be able to auto-scale itself on-demand and will be cost-effective by using the IaaS cloud. The application will provide a face recognition service to it by the user, by using cloud resources to perform deep learning on images provided by the users. The application will use cloud resources like EC2 instances, SQS, and S3 to respond to users as soon as possible. The application will scale itself and will fully harness the power of the cloud to perform the tasks efficiently while minimizing the cost.


**Architecture**

<img width="767" alt="Screenshot 2022-03-23 at 14 54 40" src="https://user-images.githubusercontent.com/37049494/159802384-fb5538e5-e2c2-4bc4-9d8c-e33ef1a32e22.png">


**Controller**

The controller will check the length of the Request Queue. The length of the queue is the summation of the visible and invisible messages in the queue. On the basis of the length of queue the controller will launch (from custom AMI), start, and stop the EC2 instances. The max number of EC2 instances running at a time is 20. It will also fetch the count the number instances on the basis of their states like running, pending, stopped and stopping, so we never exceed the max number of EC2 instances. It will keep checking for length of queue and state of instances for every 10 seconds.


**App Tier**

The app tier is implemented as a looping Python script that is run on each App Tier instance on launch. It polls the RequestQueue for a request. If request is present, it fetches the image name and encoded string of image from the Queue. The image is decoded to bytes and stored in the S3 input bucket, downloads the image into its local filesystem, classify the image using the python script provided in the project AMI, uploads image results to the S3 output bucket, deletes the image from the local filesystem, enqueues a response message containing an image name and its result into the ResponseQueue, and deletes the message from the RequestQueue. After reading the message it will sleep for 5 seconds and then again polls the RequestQueue for a request.


**Autoscaling**

Autoscaling is achieved with the help of the RequestQueue. The controller will autoscale the application on the basis of the length of RequestQueue. Only 20 EC2 instances can be deployed at once. One instances will be used by Web tier and remaining 19 instances can be used as App tier EC2 instances. Controller is deployed in Web tier instances and it will check for the length of RequestQueue. It also keeps count of the stopped, pending, running and stopping instances so we don’t run more than 20 instances at a time. If number of required instance exceed the total count of pending, running, stopped and stopping instances, then the minimum( required instance, 19) will be launched. The controller assigns unique name(“app-tier-“+GUID) to each app tier instances.
Our App tier instances will start for polling the Request Queue for messages as soon as they are in start state and will start processing the message one by one. Once it complete processing of the message, it will upload the image to input S3 bucket, result to output S3 bucket, enqueue the result to the ResponseQueue and then will delete the message from the RequestQueue. Again, it will poll the RequestQueue again and process the next image.

Suppose the user decides to upload 100 images at once. So 100 messages are enqueued in the RequestQueue. The controller will poll RequestQueue for every 10 seconds and count the number of messages in the Request Queue. Each app-tier instance will process one request at a time so 19 instances will be started and each instance will start processing the request. When the number of request falls below 19, for example requests = 10, then 9 app tier instances will be stopped and 10 app tier instances will be kept running to process the requests and when the requests drops to 0 all the instances except web tier will be stopped.
Again the user decides to upload 10 images then only 10 app-tier instances will be started and it will be stopped, start and launch on the basis of the RequestQueue. Once all the images have been processed, the controller will downscale normally by the process described above. Hence, we have achieved efficient autoscaling for our Web app.


**Testing and evaluation**

To test our application, we used the python_multithreaded_workload_generator.py file provided in the project document. Initially, we tested it with just a single image inorder to make sure the connections and workflow is working properly. Then we started increasing the loads by providing with large amounts of input. We measured the success of the attempt by the amount of time it takes to process all the requests. We also watched the number of EC2 instances doesn’t exceed the maximum limit, all requests are present in the RequestQueue, controller is properly starting and stopping the instances, each app-tier instances are sending the results to ResponseQueue, images and results are getting stored in S3 buckets, and proper response is returned to the corresponding request. We tested our application on 100 images (no app-tier launched before), which took 3 minutes and 20 seconds to evaluate, stopping the app tier instances and return its results. The largest test we attempted was with 1000 images (no app-tier launched before), which took about 35 minutes to evaluate, stopping the app tier instances, and returning it’s results. We test our application with 0 app tier instances(no app- tier instances launched before) with 19 app tier instances in stopped states before sending requests and we found the later to be faster by about 2 minutes for 1000 requests. Time taken in each test cases was found be in the acceptable time limit provided in the project document. Due to asynchronous workflow, the application (web tier and app tier) were able to handle the incoming requests and auto scale appropriately consistently. After exhausting every test case we could brainstorm, the group concluded that the application was ready for demonstration and submission.


**App-tier**

1) Start one EC2 instances with AMI provided in the project document.
2) Connect to that instances from AWS UI (user: ec2-user).
3) Install pip and boto3 onto the instances.
4) Run command “aws config” (Give required parameter after running the command)
5) Upload the ‘apptier.py’ and ‘startscript.sh’ to the EC2 instances.
6) Run command “crontab -e”
a. It will open a file edit it and add “@reboot sh startscript.sh”
b. Save and close the file.
7) Disconnect the instance
8) Create an image of this instance.
9) Terminate the instance.



**Web-Tier**

1) Start one EC2 instances with name = “Web-Tier” and AMI provided in the project document.
2) Connect to that instances from AWS UI (user: ec2-user).
3) Install pip, boto3 and aioflask onto the instances.
4) Run command “aws config” (Give required parameter after running the command)
5) Upload the “constant.py”, “webscript.sh”, controller.py”, “instances.py”, “service.py”
and “webcontroller.py” to the EC2 instances.
6) Run command “crontab -e”
a. It will open a file edit it and add “@reboot sh webscript.sh”
b. Save and close the file.
7) Disconnect the instance
8) Add the following security inbound rules!
[Uploading Screenshot 2022-03-23 at 14.50.30.png…]()
9) Start the instance.
10) Run “python3 webcontroller.py”
11) Send the request to instance using public IP of instances and port “8080”

**Web Tier**

Web tier provides API’s to the user. It is implemented in Python as a web server using the aioflask framework and boto3 python SDK are used for interaction with AWS resources. It has two routes:
1) POST /upload

  • The POST /upload route will take asynchronous request from the users.
  • It will encode the image in base64String and a message containing the image
name and encoded string is enqueued in the RequestQueue(Standard SQS).
  • It will wait for the response and will check for the correct response from the ResponseQueue(Standard SQS) on the basis of the image name and the result will be returned to user.
  
2) POST /reset

  • It will clear the RequestQueue, ResponseQueue, Input Bucket and Output
Bucket.
