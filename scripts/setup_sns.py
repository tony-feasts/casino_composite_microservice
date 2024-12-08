import boto3

sns_client = boto3.client('sns', region_name='us-east-1')
topic_name = 'casino_events_topic'

def create_sns_topic():
    response = sns_client.create_topic(Name=topic_name)
    topic_arn = response['TopicArn']
    print(f"SNS Topic ARN: {topic_arn}")
    return topic_arn

if __name__ == "__main__":
    create_sns_topic()
