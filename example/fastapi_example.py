
import json
import sys

sys.path.append(".")

from contextlib import asynccontextmanager

import boto3
from fastapi import FastAPI
from uvicorn import run

from sqs_polling.main import handler

topic_arn = "arn:aws:sns:ap-northeast-1:000000000000:test-sns-to-sqs"
client = boto3.client(
    "sns",
    endpoint_url="http://localstack:4566",
    region_name="ap-northeast-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    handler('example.simple.simple')
    yield


app = FastAPI(lifespan=lifespan)

@app.post("/")
async def some_endpoint():
    request = {
        "TopicArn": topic_arn,
        "Message": json.dumps(
            {
                "Key1": f"This is test.",
            }
        ),
        "Subject": "Test SNS to SQS",
        "MessageAttributes": {
            "Event": {"DataType": "String", "StringValue": "Create"}
        },
    }
    response = client.publish(**request)
    return {"message": response}

#### NOTE: There is no problem with using deprecated methods.
# @app.on_event('startup')
# async def startup_():
#     handler('example.simple.simple')


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8080)
