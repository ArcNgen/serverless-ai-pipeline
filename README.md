# Building IntelliDrop: An automated AI analysis pipeline with AWS S3 and SNS

A demonstration of a serverless, event-driven architecture on AWS. This project uses an AI service to analyze files uploaded to an S3 bucket and sends a notification of the results via SNS.

## High-Level Architecture

This project follows a simple, powerful serverless pattern:

1.  **Trigger:** A file (e.g., an image) is uploaded to an **Amazon S3 bucket**.
2.  **Process:** The S3 upload event automatically triggers an **AWS Lambda function**.
3.  **Analyze:** The Lambda function invokes an AI service (like **Amazon Rekognition** for images or **Amazon Comprehend** for text) to analyze the file.
4.  **Notify:** The function then publishes a summary of the analysis to an **Amazon SNS topic**.
5.  **Deliver:** The SNS topic pushes the message to subscribed endpoints, such as an email address or phone number.

## AWS Services Used

*   **AWS S3:** For object storage and to act as the trigger for our workflow.
*   **AWS Lambda:** For serverless compute, running our analysis logic without managing servers.
*   **Amazon SNS (Simple Notification Service):** To fan out notifications to subscribers.
*   **Amazon Rekognition (or other AI service):** For providing the AI-powered analysis.
*   **AWS IAM (Identity and Access Management):** For securely managing permissions between the services.

## Prerequisites

Before you begin, ensure you have the following:

*   An active AWS Account
*   The AWS CLI installed and configured with your credentials
*   Python 3.9 or later installed
*   `pip` for Python package installation

## Setup and Deployment

*(You will fill this section out as you build the project. It will include steps like...)*

1.  **Create the S3 Bucket:** `aws s3 mb s3://your-unique-bucket-name`
2.  **Create the SNS Topic:** `aws sns create-topic --name your-topic-name`
3.  **Configure IAM Role:** Create a role for the Lambda function with permissions for S3, Rekognition, and SNS.
4.  **Deploy the Lambda Function:** Package the Python code and upload it to Lambda.
5.  **Add the S3 Trigger:** Configure the S3 bucket to trigger the Lambda function on object creation.

## How to Use

1.  Subscribe to the SNS topic (e.g., with your email address).
2.  Upload a supported file (like a `.jpg` or `.png` image) to the S3 bucket.
3.  Check your email for the analysis results!
