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
    
    # 1. Get current todo list from DynamoDB
    try:
        response = todo_table.get_item(Key={'UserID': user_id})
        # If user exists, get their list; otherwise, start with an empty list
        todo_list = response.get('Item', {}).get('TodoList', [])
    except Exception as e:
        print(f"Error getting item from DynamoDB: {e}")
        return "Sorry, I couldn't access your todo list right now."
    
    # 2. Parse the command and modify the list
    parts = command.strip().split()
    action = parts[0]
    
    response_message = ""
    
    if action in ['add', 'todo', '+']:
        if len(parts) > 1:
            item_to_add = " " . join(parts[1:])
            todo_list.append(item_to_add)
            response_message = f"Added '{item_to_add}' to your todo list."
        else: 
            response_message = "Please tell me what to add. For example: 'add buy milk'."
            
    elif action in ['list', 'show', 'ls']:
        if todo_list:
            # Format the list with numbers for easy removal
            formatted_list = "\n".join([f"{i+1}. {item}" for i, item in enumerate(todo_list)])
            response_message = f"Here's your todo list:\n{formatted_list}"
        else:
            response_message = "Your todo list is empty."
    elif action in ['remove', 'delete', 'rm', '-']:
        if len(parts) > 1 and parts[1].isdigit():
            item_index = int(parts[1])-1
            if 0 <= item_index < len(todo_list):
                removed_item = todo_list.pop(item_index)
                response_message = f"Removed '{removed_item}' from your todo list."
            else:
                response_message = "That's not a valid number on your list."
        else:
            response_message = "Please specify the number of the item to remove. For example: 'remove 2'."
    else:
        response_message = "I didn't understand that command. You can say 'add', 'list', or 'remove'."
    
    # 3. Save the update list back to DynamoDB
    try:
        todo_table.put_item(Item={'UserID': user_id, 'TodoList': todo_list})
    except Exception as e:
        print(f"Error updating item in DynamoDB: {e}")
        return "Sorry, I couldn't update your todo list right now."
    
    return response_message
