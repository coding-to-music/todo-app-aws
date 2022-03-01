![cover.png](https://github.com/hpfpv/todo-app-aws/blob/main/blog-post/cover.png)

# Deploying a sample serverless to-do app on AWS

https://github.com/coding-to-music/todo-app-aws

By [H. Pierre-Francois](https://hashnode.com/@hpfpv)

https://blogs.houessou.com/sample-todo-app-aws

https://github.com/hpfpv/todo-app-aws

Hi guys! In this post, we'll be building a sample todo app on AWS with Python. We will build a web application which enables logged in visitors to manage their todo list. We will use the AWS Serverless Application Model SAM Framework to deploy the backend services - API, Lambda, DynamoDB and Cognito) and will host the frontend on S3 behind a CloudFront distribution.
The frontend is pretty basic with no fancy visuals (I am no frontend dev :p). We will try to focus on how the resources are created and deployed on AWS.

## Overview

In this post I will be going through the overall setup of the app and how I deployed it. Mostly this will be a theoretical post but I will be posting needed scripts wherever appropriate. All the code can be found in the **[GitHub repo](https://github.com/hpfpv/todo-app-aws)**.

**[Application web UI](https://todo.houessou.com)**

### About the App

Before I go into the architecture, let me describe what the app is about and what it does. The app is a todo list manager which helps a user manage and track his/her todo list along with their files or attachments. The user can also find specific todos through the search.

### Basic Functionality

![appflow.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1627647453541/A17idrTi1.png)
The image above should describe the app basic functionalities.

**User/Login Management**

_Users are able to login to the app using provided credentials. There is a self register functionality and once a user is registered, the app provides a capability to the user to login using those credentials. It also provides a logout option for the user._

**Search Todo**

_Users are able to perform a keyword search and the app shows a list of todos which contain that keyword in the name. The search only searches on todos which the logged in user has created. So it has the access boundary and doesn’t show Recipes across users._

**Add New Todo**

_Users can add new Todos to be stored in the app. There are various details which can be provided for each Todo. Users can also add notes for each Todo._

**Support for files**

_Users can upload a todo files for each Todo. The app provides a capability where user can select and upload a local file or download existing files while adding notes to a Todo. The file can be anything, from a text file to an image file. The app stores it in a S3 bucket and serves it back to the user via CloudFront._

### Application Components

Now that we have a basic functional understanding of the app, let's see how all of these functionalities translate to different technical components. Below image should provide a good overview of each layer of the app and the technical components involved in each layer.

![app-components.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1628077958693/0vhPB3Gjx.png)

Let's go through each component:

**Frontend**

_The Front end for the app is built of simple HTML and Javascript. All operations and communications with backend are performed via various REST API endpoints._

**Backend**

_Backend for the app is built Lambda Functions triggered by REST APIs. It provides various API endpoints to perform application functionalities such as adding or deleting todos, adding or deleting todo files etc. The REST APIs are built using API Gateway. The API endpoints perform all operations of connecting with the functions, authenticating, etc. CORS is enabled for the API so it only accepts requests from the frontend._

**Data Layer**

_DynamoDB Table is used to store all todos and related data. The lambda functions will be performing all Database operations connecting to the Table and getting requests from the frontend. DynamoDB is a serverless service and it provides auto scaling along with high availability._

**Authentication**

_The authentication is handled by AWS Cognito. We use a Cognito user pool to store users data. When a user logs in and a session is established with the app, the session token and related data is stored at the FrontEnd and sent over the API endpoints. API Gateway then validate the session token against Cognito and allow users to perform application operations._

**File Service**

_There is a separate service to handle files management for the application. The File service is composed of Javascript function using AWS SDK (for upload files operations), Lambda functions + API Gateway for API calls for various file operations like retrieve file info, delete file etc, S3 and DynamoDB to store files and files information. The files are served back to the user through the app using a CDN (Content Delivery Network). The CDN makes serving the static files faster and users can access/download them faster and easier._

## Application Architecture

Now that we have some information about the various components and services involved in the app, let's move on to how to place and connect these various components to get the final working application.

![architecture.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1628029946699/pOk-oRHg4.png)

### Frontend

The static _html_, _javascript_ and _css_ files generated for the website will be stored in an S3 bucket. The S3 bucket is configured to host a website and will provide an endpoint through which the app can be accessed. To have a better performance on the frontend, the S3 bucket is selected as an Origin to a CloudFront distribution. The CloudFront will act as a CDN for the app frontend and provide faster access through the app pages.

### Lambda Functions for backend services logic

All the backend logic is deployed as AWS Lambda functions. Lambda functions are totally serverless and our task is to upload our code files to create the Lambda functions along with setting other parameters. . Below are the functions which are deployed as part of the backend service:

**Todos Service**

- getTodos : _retrieve all todos for a userID_
- getTodo : _return detailed information about one todo based on the todoID attribute_
- addTodo : _create a todo for a specific user based on the userID_
- completeTodo : _update todo record and set completed attribute to TRUE based on todoID _
- addTodoNotes : _update todo record and set the notes attribute to the specified value based on todoID_
- deleteTodo : \*delete a todo for a specific user based on the userID and todoID

* **Files Service**

- getTodoFiles : _retrieve all files which belong to a specified todo_
- addTodoFiles : _add files to as attachment to a specified todo_
- deleteTodoFiles: _delete selected file for specified todo_

### API Gateway to expose Lambda Functions

To expose the Lambda functions and make them accessible by the Frontend, AWS API Gateway is deployed. API Gateway defines all the endpoints for the APIs and route the requests to proper Lambda function in the backend. These API gateway endpoints are called by the frontend. Each application service has its own API (keeping services as separate as possible for decoupling purpose) with deployed routes as follow:

**Todos Service**

- getTodos : /{**userID**}/todos
- getTodo : /{**userID**}/todos/{**todoID**}
- deleteTodo : /{**userID**}/todos/{**todoID**}/delete
- addTodo : /{**userID**}/todos/add
- completeTodo : /{**userID**}/todos/{**todoID**}/complete
- addTodoNotes : /{**userID**}/todos/{**todoID**}/addnotes

**Files Service**

- getTodoFiles : /{**todoID**}/files
- addTodoFiles : /{**todoID**}/files/upload
- deleteTodoFiles : /{**todoID**}/files/{**fileID**}/delete

The addTodoFiles API route triggers the addTodoFiles function which only record the file information like fine name and file path/key to a DynamoDB table. The same table is queried by the getTodoFiles function to display returned files information.
The actual operation to upload the files to S3 is perform by a Javascript function in the Frontend code. I found it better to do it that way to prevent large amount of data going through the lambda functions and thus increasing response time and cost.

### Database

DynamoDB tables are used to serve as database. We have two tables for respectively the Todos Service and the Files Service.
The search functionality of the app is handled by simple DynamoDB query requests. We can deployed a DynamoDB Accelerator in front of the tables to increase performance if needed. Below is the tables configuration:

**Todos Service**
To keep things simple, each document in DynamoDB will represent one todo with attributes as follow:

- todoID : _unique number identifying todo, will serve as primary key_
- userID : _ID of the user who created the todo, will serve as sort key_
- dateCreated : _date todo has been created, today's date_
- dateDue : _date the todo is due, user provided_
- title : _todo title, user provided_
- description : _todo description, user provided_
- notes : _additional notes for todo, can be added anytime after todo is created, blank by default_
- _completed_ : _true or false if todo is marked as completed_

**Files Service**

- fileID : _unique number identifying file, will serve as primary key_
- todoID : _ID of belonging todo item, will serve as sort key_
- fileName : _name of the uploaded file_
- filePath : _URL of the uploaded file for downloads_

### File Storage

To support the file management capability of the application, a file storage need to be deployed. I am using an S3 bucket as the storage for the files which are uploaded from the app. The file service API calls the AWS S3 API to store the files in the bucket. To serve the files back to the user, a CloudFront distribution is created with the S3 bucket as the origin. This will serve as the CDN to distribute the static files faster to the end users.

## IaC and Deployment Method

The application backend services are defined as SAM templates. Each service has his own template and resources are configured to be as independent as possible.
I am using automated deployments for the whole application environment - frontend and 2 backend services. Each service is deployed using a separate deployment pipeline to maintain optimal decoupling.
The components below are used as part of the deployment pipeline:

- One GitHub Repository for code commits
- A separate branch for Prod changes (master branch as Dev)
- Various paths, one per service - Frontend, Backend Todos Service and Backend Files Service
- Any commit to a service path in a specified branch (Prod or Dev) automatically tests deploys changes to the service in the appropriate environment.
- GitHub Actions backed by docker containers to build and deploy services

**FrontEnd**

![frontend-pipeline.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1628077668965/DMv5htTiG.png)

**Backend**

![backend-pipeline.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1628077651575/cMRfCM8MB.png)

## Takeaways

Hopefully, I was able to describe in detail about the system architecture which I would use for a basic todo-list management app. This application is designed solely for training purposes and there is a lot of room for improvement. I will continue working on making the deployment more secure, HA and fault tolerant.
This post should give you a good idea about how to design a basic full stack and fully serverless architecture for an app using the microservices patter.

# My Changes

### search and replace the following:

backend/attachments-service/samconfig.toml

```java
stack_name = "sam-todo-app"
s3_prefix = "sam-todo-app"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket-1hniiozy06797"
```

backend/main-service/samconfig.toml

```java
stack_name = "sam-todo-app"
s3_prefix = "sam-todo-app"
s3_bucket = "aws-sam-cli-managed-default-samclisourcebucket-1hniiozy06797"
```

Manually created the following S3 buckets:

```java
cd backend/main-service

sam build
```

Output:

```java
Building codeuri: /mnt/volume_nyc1_01/todo-app-aws/backend/main-service/functions runtime: python3.8 metadata: {} architecture: x86_64 functions: ['getTodos', 'getTodo', 'deleteTodo', 'addTodo', 'completeTodo', 'addTodoNotes']
Running PythonPipBuilder:ResolveDependencies
Running PythonPipBuilder:CopySource

Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml

Commands you can use next
=========================
[*] Invoke Function: sam local invoke
[*] Test Function in the Cloud: sam sync --stack-name {stack-name} --watch
[*] Deploy: sam deploy --guided


SAM CLI update available (1.40.0); (1.38.1 installed)
To download: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
```

Attempt to deploy the application to AWS:

Output:

```java

tmc@docker-ubuntu-s-1vcpu-1gb-nyc1-01:/mnt/volume_nyc1_01/todo-app-aws/backend/main-service$ sam deploy --guided

Configuring SAM deploy
======================

        Looking for config file [samconfig.toml] :  Found
        Reading default arguments  :  Success

        Setting default arguments for 'sam deploy'
        =========================================
        Stack Name [sam-todo-app2]:
        AWS Region [us-east-1]:
        #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
        Confirm changes before deploy [y/N]: y
        #SAM needs permission to be able to create roles to connect to the resources in your template
        Allow SAM CLI IAM role creation [Y/n]: y
        #Preserves the state of previously provisioned resources when an operation fails
        Disable rollback [y/N]: y
        Save arguments to configuration file [Y/n]: y
        SAM configuration file [samconfig.toml]:
        SAM configuration environment [default]:

        Looking for resources needed for deployment:
        Creating the required resources...
        Successfully created!
         Managed S3 bucket: aws-sam-cli-managed-default-samclisourcebucket-1hniiozy06797
         A different default S3 bucket can be set in samconfig.toml

        Saved arguments to config file
        Running 'sam deploy' for future deployments will use the parameters saved above.
        The above parameters can be changed by modifying samconfig.toml
        Learn more about samconfig.toml syntax at
        https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-config.html

Uploading to sam-todo-app2/47902f40ff47f9f7366d5ac33da53d24  9560299 / 9560299  (100.00%)
File with same data already exists at sam-todo-app2/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app2/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app2/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app2/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app2/47902f40ff47f9f7366d5ac33da53d24, skipping upload

        Deploying with following values
        ===============================
        Stack name                   : sam-todo-app2
        Region                       : us-east-1
        Confirm changeset            : True
        Disable rollback             : True
        Deployment s3 bucket         : aws-sam-cli-managed-default-samclisourcebucket-1hniiozy06797
        Capabilities                 : ["CAPABILITY_IAM"]
        Parameter overrides          : {}
        Signing Profiles             : {}
```

### Subsequent builds

```java
cd backend/main-service

sam build

sam deploy
```

Output:

```java
File with same data already exists at sam-todo-app/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app/47902f40ff47f9f7366d5ac33da53d24, skipping upload
File with same data already exists at sam-todo-app/47902f40ff47f9f7366d5ac33da53d24, skipping upload

        Deploying with following values
        ===============================
        Stack name                   : sam-todo-app
        Region                       : us-east-1
        Confirm changeset            : True
        Disable rollback             : True
        Deployment s3 bucket         : aws-sam-cli-managed-default-samclisourcebucket-1hniiozy06797
        Capabilities                 : ["CAPABILITY_IAM"]
        Parameter overrides          : {}
        Signing Profiles             : {}

Initiating deployment
=====================
File with same data already exists at sam-todo-app/ed387b0da5a7d1ff31828f7a4cf02329.template, skipping upload

Waiting for changeset to be created..

CloudFormation stack changeset
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Operation                                                     LogicalResourceId                                             ResourceType                                                  Replacement
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
+ Add                                                         MainHttpApidevStage                                           AWS::ApiGatewayV2::Stage                                      N/A
+ Add                                                         MainHttpApi                                                   AWS::ApiGatewayV2::Api                                        N/A
+ Add                                                         TodoTable                                                     AWS::DynamoDB::Table                                          N/A
+ Add                                                         TodoUserPoolClient                                            AWS::Cognito::UserPoolClient                                  N/A
+ Add                                                         TodoUserPoolDomain                                            AWS::Cognito::UserPoolDomain                                  N/A
+ Add                                                         TodoUserPool                                                  AWS::Cognito::UserPool                                        N/A
+ Add                                                         addTodoNotesRole                                              AWS::IAM::Role                                                N/A
+ Add                                                         addTodoNotesaddTodoNotesApiPermission                         AWS::Lambda::Permission                                       N/A
+ Add                                                         addTodoNotes                                                  AWS::Lambda::Function                                         N/A
+ Add                                                         addTodoRole                                                   AWS::IAM::Role                                                N/A
+ Add                                                         addTodoaddTodoApiPermission                                   AWS::Lambda::Permission                                       N/A
+ Add                                                         addTodo                                                       AWS::Lambda::Function                                         N/A
+ Add                                                         completeTodoRole                                              AWS::IAM::Role                                                N/A
+ Add                                                         completeTodocompleteTodoApiPermission                         AWS::Lambda::Permission                                       N/A
+ Add                                                         completeTodo                                                  AWS::Lambda::Function                                         N/A
+ Add                                                         deleteTodoRole                                                AWS::IAM::Role                                                N/A
+ Add                                                         deleteTododeleteTodoApiPermission                             AWS::Lambda::Permission                                       N/A
+ Add                                                         deleteTodo                                                    AWS::Lambda::Function                                         N/A
+ Add                                                         getTodoRole                                                   AWS::IAM::Role                                                N/A
+ Add                                                         getTodogetTodoApiPermission                                   AWS::Lambda::Permission                                       N/A
+ Add                                                         getTodosRole                                                  AWS::IAM::Role                                                N/A
+ Add                                                         getTodosgetTodosApiPermission                                 AWS::Lambda::Permission                                       N/A
+ Add                                                         getTodos                                                      AWS::Lambda::Function                                         N/A
+ Add                                                         getTodo                                                       AWS::Lambda::Function                                         N/A
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Changeset created successfully. arn:aws:cloudformation:us-east-1:708090526287:changeSet/samcli-deploy1646117504/9da03b0f-3b24-4ff4-98dd-64f9c7f5209a


Previewing CloudFormation changeset before deployment
======================================================
Deploy this changeset? [y/N]: y

2022-03-01 06:52:01 - Waiting for stack create/update to complete

CloudFormation events from stack operations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ResourceStatus                                                ResourceType                                                  LogicalResourceId                                             ResourceStatusReason
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
UPDATE_IN_PROGRESS                                            AWS::CloudFormation::Stack                                    sam-todo-app                                                  No export named sam-todo-app-attachments-service-
                                                                                                                                                                                          TodoFilesTable found
UPDATE_FAILED                                                 AWS::CloudFormation::Stack                                    sam-todo-app                                                  -
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Failed to deploy. Automatic rollback disabled for this deployment.

Actions you can take next
=========================
[*] Fix issues and try deploying again
[*] Roll back stack to the last known stable state: aws cloudformation rollback-stack --stack-name sam-todo-app

Error: Failed to create/update the stack: sam-todo-app, Waiter StackUpdateComplete failed: Waiter encountered a terminal failure state: For expression "Stacks[].StackStatus" we matched expected path: "UPDATE_FAILED" at least once
```

### deploy backend/attachments-service

```java
cd backend/attachments-service

sam build

sam deploy
```

```java
File with same data already exists at sam-todo-app-attachments-service/d969942f2e70a500abb42539c0bcb71f, skipping upload
File with same data already exists at sam-todo-app-attachments-service/d969942f2e70a500abb42539c0bcb71f, skipping upload
File with same data already exists at sam-todo-app-attachments-service/d969942f2e70a500abb42539c0bcb71f, skipping upload

        Deploying with following values
        ===============================
        Stack name                   : sam-todo-app-attachments-service
        Region                       : us-east-1
        Confirm changeset            : True
        Disable rollback             : True
        Deployment s3 bucket         : aws-sam-cli-managed-default-samclisourcebucket-1hniiozy06797
        Capabilities                 : ["CAPABILITY_NAMED_IAM"]
        Parameter overrides          : {}
        Signing Profiles             : {}

Initiating deployment
=====================
File with same data already exists at sam-todo-app-attachments-service/8da6c9971a7febe82079d940b670e41c.template, skipping upload

Waiting for changeset to be created..

CloudFormation stack changeset
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Operation                                                     LogicalResourceId                                             ResourceType                                                  Replacement
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
+ Add                                                         FilesApidevStage                                              AWS::ApiGatewayV2::Stage                                      N/A
+ Add                                                         FilesApi                                                      AWS::ApiGatewayV2::Api                                        N/A
+ Add                                                         TodoFilesBucketCF                                             AWS::CloudFront::Distribution                                 N/A
+ Add                                                         TodoFilesBucketOAI                                            AWS::CloudFront::CloudFrontOriginAccessIdentity               N/A
+ Add                                                         TodoFilesBucketPolicy                                         AWS::S3::BucketPolicy                                         N/A
+ Add                                                         TodoFilesBucket                                               AWS::S3::Bucket                                               N/A
+ Add                                                         TodoFilesTable                                                AWS::DynamoDB::Table                                          N/A
+ Add                                                         TodoIdentityPoolRoleAttachment                                AWS::Cognito::IdentityPoolRoleAttachment                      N/A
+ Add                                                         TodoIdentityPoolRole                                          AWS::IAM::Role                                                N/A
+ Add                                                         TodoIdentityPool                                              AWS::Cognito::IdentityPool                                    N/A
+ Add                                                         addTodoFilesRole                                              AWS::IAM::Role                                                N/A
+ Add                                                         addTodoFilesaddTodoApiPermission                              AWS::Lambda::Permission                                       N/A
+ Add                                                         addTodoFiles                                                  AWS::Lambda::Function                                         N/A
+ Add                                                         deleteTodoFileRole                                            AWS::IAM::Role                                                N/A
+ Add                                                         deleteTodoFiledeleteTodoApiPermission                         AWS::Lambda::Permission                                       N/A
+ Add                                                         deleteTodoFile                                                AWS::Lambda::Function                                         N/A
+ Add                                                         getTodoFilesRole                                              AWS::IAM::Role                                                N/A
+ Add                                                         getTodoFilesgetFilesApiPermission                             AWS::Lambda::Permission                                       N/A
+ Add                                                         getTodoFiles                                                  AWS::Lambda::Function                                         N/A
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Changeset created successfully. arn:aws:cloudformation:us-east-1:708090526287:changeSet/samcli-deploy1646117576/50095e45-e0c2-4c07-b47b-878d19387511


Previewing CloudFormation changeset before deployment
======================================================
Deploy this changeset? [y/N]: y

2022-03-01 06:53:11 - Waiting for stack create/update to complete

CloudFormation events from stack operations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ResourceStatus                                                ResourceType                                                  LogicalResourceId                                             ResourceStatusReason
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
UPDATE_IN_PROGRESS                                            AWS::CloudFormation::Stack                                    sam-todo-app-attachments-service                              No export named sam-todo-app-TodoUserPoolClient found
UPDATE_FAILED                                                 AWS::CloudFormation::Stack                                    sam-todo-app-attachments-service                              -
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Failed to deploy. Automatic rollback disabled for this deployment.

Actions you can take next
=========================
[*] Fix issues and try deploying again
[*] Roll back stack to the last known stable state: aws cloudformation rollback-stack --stack-name sam-todo-app-attachments-service

Error: Failed to create/update the stack: sam-todo-app-attachments-service, Waiter StackUpdateComplete failed: Waiter encountered a terminal failure state: For expression "Stacks[].StackStatus" we matched expected path: "UPDATE_FAILED" at least once
```
