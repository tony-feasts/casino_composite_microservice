import boto3
import json
from os import getenv
from dotenv import load_dotenv

load_dotenv()

sqs_client = boto3.client('sqs', region_name=getenv('AWS_REGION'))
LOGIN_QUEUE_URL = getenv('LOGIN_QUEUE_URL')

def process_login_event():
    """
    Processes login events from the SQS queue.
    """
    while True:
        response = sqs_client.receive_message(
            QueueUrl=LOGIN_QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        messages = response.get('Messages', [])
        for message in messages:
            event = json.loads(message['Body'])
            if event['event_type'] == "USER_LOGIN":
                print(f"Processing login for user: {event['username']}")
            # Delete the message after processing
            sqs_client.delete_message(
                QueueUrl=LOGIN_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
