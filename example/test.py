import json
from pprint import pprint

import boto3

topic_arn = "arn:aws:sns:ap-northeast-1:000000000000:test-sns-to-sqs.fifo"
client = boto3.client(
    "sns",
    endpoint_url="http://localstack:4566",
    region_name="ap-northeast-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)


def main(count: int):
    for i in range(count):
        request = {
            "TopicArn": topic_arn,
            "Message": json.dumps(
                {
                    "Key1": f"This is test {i}.",
                }
            ),
            "Subject": "Test SNS to SQS",
            "MessageGroupId": "Group1" if i % 2 == 0 else "Group2",
        }

        response = client.publish(**request)
        pprint(response)


if __name__ == "__main__":
    import sys

    count = sys.argv[1]
    main(int(count))
