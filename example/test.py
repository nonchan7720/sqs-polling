import json
from pprint import pprint

import boto3

topic_arn = "arn:aws:sns:ap-northeast-1:000000000000:test-sns-to-sqs"
client = boto3.client(
    "sns",
    endpoint_url="http://localstack:4566",
    region_name="ap-northeast-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)

request = {
    "TopicArn": topic_arn,
    "Message": json.dumps(
        {
            "Key1": "This is test.",
        }
    ),
    "Subject": "Test SNS to SQS",
}

response = client.publish(**request)
pprint(response)
