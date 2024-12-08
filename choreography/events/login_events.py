import boto3
import json
from os import getenv
from dotenv import load_dotenv

load_dotenv()

sns_client = boto3.client('sns', region_name=getenv('AWS_REGION'))
LOGIN_TOPIC_ARN = getenv('LOGIN_TOPIC_ARN')

def publish_login_event(username):
    """
    Publishes a login event to the SNS topic.
    """
    event = {
        "event_type": "USER_LOGIN",
        "username": username
    }
    response = sns_client.publish(
        TopicArn=LOGIN_TOPIC_ARN,
        Message=json.dumps(event),
        Subject="UserLoginEvent"
    )
    return response['MessageId']
