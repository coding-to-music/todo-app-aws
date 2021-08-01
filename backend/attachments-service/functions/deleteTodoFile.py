import boto3
import json
import os
import logging
from collections import defaultdict
from boto3.dynamodb.conditions import Key

dynamo = boto3.client('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def deleteTodosFileS3(filePath):
    response = s3.delete_object(
        Bucket=os.environ["TODOFILES_BUCKET"],
        Key=filePath,
    )
    logging.info(f"{filePath} deleted from S3")
    return response
   
def deleteTodosFileDynamo(fileID, todoID):
    response = dynamo.delete_item(
        TableName=os.environ['TODOFILES_TABLE'],
        Key={
            'fileID': {
                'S': fileID
            },
            'todoID': {
                'S': todoID
            },
        }
    )
    logging.info(f"{fileID} deleted from DynamoDB")
    return response
def lambda_handler(event, context):
    logger.info(event)
    eventBody = json.loads(event["body"])
    fileID = event["pathParameters"]["fileID"]
    filePath = eventBody["filePath"]
    todoID = event["pathParameters"]["fileID"]

    print(f"deleting file {fileID}")
    deleteTodosFileS3(filePath)
    deleteTodosFileDynamo(fileID,todoID)

    responseBody = {}
    responseBody["status"] = "success"
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': 'https://todo.houessou.com',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET, DELETE, POST',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(responseBody)  
    }