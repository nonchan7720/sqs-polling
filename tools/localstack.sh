#!/bin/bash

awslocal sns create-topic --name test-sns-to-sqs
awslocal sqs create-queue --queue-name test-sns-to-sqs

awslocal sns subscribe --topic-arn arn:aws:sns:ap-northeast-1:000000000000:test-sns-to-sqs --protocol sqs --notification-endpoint http://localhost:4566/000000000000/test-sns-to-sqs
