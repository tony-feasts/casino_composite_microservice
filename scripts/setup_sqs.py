import boto3

sqs_client = boto3.client('sqs', region_name='us-east-1')
queue_name = 'casino_login_queue'

def create_sqs_queue():
    response = sqs_client.create_queue(QueueName=queue_name)
    queue_url = response['QueueUrl']
    print(f"SQS Queue URL: {queue_url}")
    return queue_url

if __name__ == "__main__":
    create_sqs_queue()
