# Project: Serverless SMS AI Assistant with Twilio

This project is a powerful, SMS-based AI assistant built entirely on a serverless AWS architecture. It can answer general knowledge questions, analyze images, and manage a personal to-do list, all through text messages sent and received via **Twilio**.

The application's backend is defined and deployed using the **AWS Serverless Application Model (SAM)**.

## Features

*   **Conversational Q&A:** Ask questions and get answers from Anthropic's Claude 3 Sonnet model via Amazon Bedrock.
*   **Image Analysis:** Send an MMS with an image to identify objects, scenes, and concepts using Amazon Rekognition.
*   **To-Do List Management:** Add, view, and remove items from a personal to-do list.
*   **Persistent Storage:** Each user's to-do list is stored in a DynamoDB table, identified by their phone number.
*   **Fully Serverless:** The entire backend runs on AWS Lambda, triggered by an API Gateway endpoint.
*   **Infrastructure as Code (IaC):** All required AWS resources are defined in a `template.yaml` file for automated, repeatable deployments.
*   **Unit Tested:** The application logic is verified with a comprehensive suite of unit tests using Python's `unittest` framework and the `moto` library for mocking AWS services.

## Architecture

1.  **User Input (SMS/MMS):** A user sends a message from their personal phone to a Twilio-provided phone number.
2.  **Twilio Webhook:** Twilio receives the message and forwards the data (sender's number, message body, media URL) via an **HTTP POST webhook** to our application's endpoint.
3.  **API Gateway:** The **Amazon API Gateway** endpoint receives the webhook and triggers the Lambda function.
4.  **Lambda Function:** The single **AWS Lambda function** contains all the application logic:
    *   It parses the incoming request from Twilio to determine the user's intent.
    *   For questions, it invokes a foundation model via **Amazon Bedrock**.
    *   For images, it downloads the image and sends it to **Amazon Rekognition** for analysis.
    *   For to-do commands, it performs CRUD operations on **Amazon DynamoDB**.
5.  **Backend Services:**
    *   **Amazon Bedrock:** Provides access to the Claude 3 Sonnet foundation model.
    *   **Amazon Rekognition:** Provides image detection capabilities.
    *   **Amazon DynamoDB:** Stores user-specific to-do lists.
6.  **Response:** The Lambda function formats a reply and sends it back to the API Gateway. Twilio receives this response and forwards it as a reply SMS to the user's phone.

## Project Structure

```
.
├── lambda_function/      # Contains the Lambda function code
│   ├── main.py           # Core application logic
│   └── requirements.txt  # Python dependencies (requests)
├── tests/                # Unit tests
│   └── test_main.py
├── .gitignore
├── README.md
└── template.yaml         # AWS SAM template defining all resources
```

## Setup, Build, and Deployment

### Prerequisites

*   An AWS account with configured credentials for the AWS CLI.
*   Python 3.12.
*   **AWS SAM CLI:** The command-line interface for building and deploying serverless applications.
    *   If you run `sam --version` and get a "command not found" error, you will need to [install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
*   **A Twilio Trial Account:** Required for getting a free, testable phone number.

### Step 1: Build the AWS Backend

The `sam build` command packages the Lambda function code and its dependencies. Run this command from the project root:

```bash
sam build
```
This creates a `.aws-sam` directory with the packaged application, ready for deployment.

**Important:** If you make any changes to `template.yaml`, you must run `sam build` again to ensure the changes are packaged before you deploy.

### Step 2: Deploy the Backend with AWS SAM

The `sam deploy --guided` command will deploy the application's backend (Lambda, API Gateway, DynamoDB, IAM Role) to your AWS account.

```bash
sam deploy --guided
```
During the guided deployment:
*   **Stack Name:** Give your application a unique name (e.g., `sms-ai-assistant`).
*   **AWS Region:** Choose your desired region.
*   **AICompanionFunction has no authentication...**: This is expected. Answer `Y` (yes) to acknowledge the warning. Our API is intended to be called by the Twilio webhook.
*   **Save arguments to samconfig.toml**: Answering `Y` (yes) is recommended.

### Step 3: Locate Your API URL

Once deployment is successful, you need the public URL of your API Gateway. If the `sam deploy` output does not display the `ApiUrl` value, you can find it in the AWS Console:

1.  Navigate to the **AWS CloudFormation** console.
2.  Select the stack you just created (e.g., `sms-ai-assistant`).
3.  Click on the **Outputs** tab.
4.  The `ApiUrl` value will be listed there. **Copy this URL for the next step.**

### Step 4: Configure Twilio

Due to complex carrier registration rules (A2P 10DLC), using a Twilio trial account is the fastest way to test this project.

1.  **Sign up for a Twilio Trial Account:** Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio) and create a free account. You will need to verify your email and a personal phone number for testing.
2.  **Get a Trial Phone Number:**
    *   From your Twilio Console dashboard, click the button to **Get a trial phone number**.
    *   Accept the number that Twilio suggests.
3.  **Configure the Messaging Webhook:**
    *   In the Twilio Console, search for **"Phone Numbers"** and go to your **Active Numbers**.
    *   Click on your new trial number.
    *   Scroll down to the **"Messaging"** section.
    *   Find the line **"When a message comes in"**.
    *   Set the first dropdown to **`Webhook`**.
    *   In the text box, paste the **`ApiUrl`** you copied from CloudFormation.
    *   Set the second dropdown to **`HTTP POST`**.
    *   Click **Save**.

Your application is now fully configured! You can test it by sending an SMS or MMS from your verified personal phone to your new Twilio number.

## How to Use

*   **To ask a question:** `What is the largest planet in our solar system?`
*   **To analyze an image:** Send an image via MMS.
*   **To add a to-do:** `add buy groceries`
*   **To view your list:** `list`
*   **To remove a to-do:** `remove 1`

## Troubleshooting

If your messages are not receiving replies, the two most important places to check are the Twilio logs and the Lambda function's CloudWatch logs.

### 1. Check Twilio Logs

1.  In the Twilio Console, go to **Monitor -> Logs -> Messaging**.
2.  Click on the log for the incoming message.
3.  Look at the **"Request Inspector"** to see the `HTTP Response` that Twilio received from your API Gateway.
    *   **`502 Bad Gateway` or `5xx` errors:** This means your Lambda function is crashing. Proceed to check the CloudWatch logs.
    *   **`Timeout` error:** This means the Lambda function took too long to respond (longer than Twilio's 15-second limit). This often happens on the first "cold start". Try sending the message again. If it persists, check the CloudWatch logs for performance issues.

### 2. Check AWS CloudWatch Logs

This is the best way to see errors from the Lambda function itself.

1.  In the AWS Console, navigate to **CloudWatch -> Logs -> Log groups**.
2.  Find the log group for your function (e.g., `/aws/lambda/sms-ai-assistant-AICompanionFunction-...`).
3.  Click on the most recent log stream.
4.  Look for any errors or `Traceback` messages. A common initial error is an `AccessDeniedException` from Bedrock, which means you need to enable model access in the Bedrock console.

### 3. Testing the Lambda Function Directly

This test bypasses Twilio and API Gateway to confirm if your core AWS backend is working correctly.

1.  Navigate to the **AWS Lambda** console and click on your function.
2.  Select the **"Test"** tab.
3.  **Create a new test event:**
    *   **Event name:** `TwilioTest`
    *   **Event JSON:** Delete the default content and paste in the following JSON, which simulates a request from Twilio.
    ```json
    {
      "version": "2.0",
      "routeKey": "$default",
      "rawPath": "/",
      "rawQueryString": "",
      "headers": {},
      "requestContext": {
        "accountId": "123456789012",
        "apiId": "yourapi",
        "domainName": "yourapi.execute-api.us-east-1.amazonaws.com",
        "domainPrefix": "yourapi",
        "http": {
          "method": "POST",
          "path": "/",
          "protocol": "HTTP/1.1",
          "sourceIp": "127.0.0.1",
          "userAgent": "TwilioProxy/1.1"
        },
        "requestId": "test-request-id",
        "routeKey": "$default",
        "stage": "$default",
        "timeEpoch": 1674642600000
      },
      "body": "From=%2B15551234567&To=%2B15557654321&Body=What+is+the+capital+of+France%3F&NumMedia=0",
      "isBase64Encoded": false
    }
    ```
4.  Click **Save**, then click the **Test** button.
    *   **Success:** If the execution result is green and the response `body` contains the correct answer, your entire AWS backend is working perfectly. The issue is likely a timeout or a configuration problem between Twilio and API Gateway.
    *   **Failure:** If the result is red, the function logs will show the exact error in your code or IAM permissions.

## Running the Unit Tests

1.  **Install Dependencies:**
    ```bash
    pip install boto3 moto requests
    ```

2.  **Run the tests:**
    From the project's root directory, run:
    ```bash
    python3 -m unittest tests/test_main.py
    ```
