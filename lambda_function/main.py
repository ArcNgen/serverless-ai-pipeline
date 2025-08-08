# This code is part of an AWS Lambda function that processes events from an SQS queue.
# It retrieves messages from the queue, processes them, and sends the results to be processed by aws ai services.
# The function uses the AWS SDK for Python (Boto3) to interact with AWS services 
import boto3 
import logging
import json
import os