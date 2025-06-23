#!/usr/bin/env bash
# The script pre-configures the SNS and SQS queues and their subscriptions.

# enable debug
sleep 5;

set -x

echo "Creating stack..."
awslocal cloudformation deploy --stack-name stack \
    --template-file /etc/localstack/init/ready.d/localstack-cf.yml --region ${AWS_REGION}
