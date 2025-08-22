import boto3
import os
import json
import re #using regular expressions for simple command parsing

# --- AWS Service clients ---
# Initialize clients outside the handler for reuse
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')
reckognition_client = boto3.client('rekognition')

# --- Configuration ---
# Load table name from Lambda environment variables
TODO_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'AI-Assistant-Users')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

# Connect to the DynamoDB table
todo_table = dynamodb.Table(TODO_TABLE_NAME)

# --- Main handler ---
def lambda_handler(event, context):
    """
    Main entry point for the lambda function
    Parse the incoming request and routes to the correct handler
    """
    
    print("Received event:", json.dumps(event))
    
    # The request body from API Gateway (integrated with Twilio/Pinpoint)
    # will contain the message details. This parsing may need adjustment
    # based on your exact API Gateway and messaging service setup.
    # For Twilio, it's often a URL-encoded form body.
    body = event.get('body', '')
    
    # A simple way to parse a form-encoded body
    params = dict(p.split('=') for p in body.split('&'))
    user_id = params.get('From', '') # User's phone number
    message_body = params.get('Body', '').lower().strip()
    num_media = int(params.get('NumMedia', '0'))
    
    response_message = ""
    
    # --- Intent Routing ---
    if num_media > 0:
        media_url = params.get('MediaUrl0', '')
        response_message = handle_image_analysis(user_id, media_url)
    elif message_body.startswith(('add', 'todo', 'list', 'show', 'remove', 'delete')):
        response_message = handle_todo_list(user_id, message_body)
    else:
        response_message = handle_question(user_id, message_body)
        
# IMAGE HANDLER =========================================================================
def handle_image_analysis(user_id, image_url):
    """
    Analyzes an image from a URL using Rekognition. 
    NOTE: Rekognition doesn't work with URLs directly. This is a placeholder
    for the logic you'll need to write to download the image first.
    """
    
    print(f"Handling image analysis for {user_id} from {image_url}")
    # TODO:
    # 1. Use a library like 'requests to download the image from image_url.
    #    image_bytes = requests.get(image_url).content
    # 2. Call Rekognition's detect_labels with the image bytes:
    #    response = rekognition_client.detect_labels(Image={'Bytes': image_bytes})
    # 3. Format the labels from the response into a friendly message.
    return "Image analysis freature is under construction."

# QUESTION HANDLER =======================================================================
def handle_question(user_id, question):
    """
    Answer a general question using Amazon Bedrock.
    """
    print(f"Handling question '{question}' for {user_id}")
    # TODO:
    # 1. Construct the prompt for the Bedrock model. 
    #    (This varies by model, for Claude it's a JSON object).
    # 2. Invoke the model using bedrock_runtime.invoke_model().
    # 3. Parse the streaming response from Bedrock to get the answer text.
    # 4. Return the answer. 
    return "Q&A feature is under construction."

# TODO LIST HANDLER ======================================================================
def handle_todo_list(user_id, command):
    """ 
    Manage the user's todo list in DynamoDB.
    """
    print(f"Handling todo command '{command}' for {user_id}")
    # TODO:
    # 1. Get the user's current list from DynamoDB using todo_table.get_item(). 
    # 2. Parse the command (e.g. 'add buy milk', 'remove 2').
    # 3. Modify the list object in your python code (add, remove item).
    # 4. Save the updated list back to DynamoDB using todo_table.put_item().
    # 5. Format a confirmation message (e.g. "Added 'buy milk' to your list").
    return "Todo list feature is under construction."
