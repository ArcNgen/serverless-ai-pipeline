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

If you don't receive an SMS reply, follow these steps in order.

### Step 1: Check the Twilio Message Log

This tells you if the connection from Twilio to your AWS application is working.

1.  In the Twilio Console, go to **Monitor -> Logs -> Messaging**.
2.  Click on the log for the incoming message you sent.
3.  Look for any error messages. Common issues include:
    *   **`Timeout` error:** This means the Lambda function took too long to respond (longer than Twilio's 15-second limit). This often happens on the first "cold start". **Try sending the message again**, as the second attempt on a "warm" function is much faster.
    *   **`502 Bad Gateway` error:** This means your Lambda function received the request but crashed. Proceed to Step 2.
    *   **XML Schema Warning:** If you see a warning about invalid XML, it means your Lambda function is not returning a correctly formatted TwiML response. Ensure the `body` of your function's return statement looks like `<Response><Message>Your text here</Message></Response>`.

### Step 2: Check the AWS CloudWatch Logs

This is the best way to see the live output and errors from the Lambda function itself.

1.  In the AWS Console, navigate to **CloudWatch -> Logs -> Log groups**.
2.  Find the log group for your function (e.g., `/aws/lambda/sms-ai-assistant-AICompanionFunction-...`).
3.  Click on the most recent log stream.
4.  Look for any errors or `Traceback` messages. A common initial error is an **`AccessDeniedException`** from Bedrock. This means you must enable model access for your AWS account:
    *   In the **Amazon Bedrock** console, go to **Model access** (at the bottom of the left menu).
    *   Click **Manage model access**.
    *   Check the box for **Anthropic** and submit the form with the use case details. You must wait for the status to become **"Access granted"**.

### Step 3: Test the Lambda Function Directly

This test bypasses Twilio and API Gateway to confirm if your core AWS backend is working correctly.

1.  Navigate to the **AWS Lambda** console and click on your function.
2.  Select the **"Test"** tab.
3.  **Create a new test event:**
    *   **Event name:** `TwilioTest`
    *   **Event JSON:** Delete the default content and paste in the JSON provided in the "Running the Unit Tests" section below.
4.  Click **Save**, then click the **Test** button.
    *   **Success:** If the execution result is green and the response `body` contains a valid TwiML string, your entire AWS backend is working perfectly.
    *   **Failure:** If the result is red, the function logs will show the exact error in your code or IAM permissions.

### Important Note on Twilio Trial Accounts

Twilio trial accounts have a key limitation for sending messages to the US due to carrier A2P 10DLC regulations. You may see a warning in your Twilio logs that says **"Message from an Unregistered Number"**.

*   This means your backend is working correctly and successfully told Twilio to send a reply.
*   However, the carrier blocked the final message because your trial number is not registered.
*   **This is expected behavior.** For this project, you can confirm your application is working by checking the CloudWatch logs for a successful run, even if you don't receive the final SMS. To enable replies, you would need to upgrade your Twilio account and complete the A2P 10DLC registration process.

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
