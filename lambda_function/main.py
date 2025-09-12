import boto3
import os
import json
import re #using regular expressions for simple command parsing
import requests

# --- AWS Service clients ---
# Initialize clients outside the handler for reuse
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')
rekognition_client = boto3.client('rekognition')

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
    """
    
    print(f"Handling image analysis for {user_id} from {image_url}")
    
    try:
        # 1. Use requests to download the image from the URL
        response = requests.get(image_url, timeout=10)
        response.raise_for_status() # Raises an exception for bad status codes
        image_bytes = response.content
        
        # 2. Call Rekognition's detect_labels with the image bytes.
        rekognition_response = rekognition_client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=10,
            MinConfidence=75
        )
        
        # 3. Format the labels from the response into a friendly message.
        labels = rekognition_response.get('Labels', [])
        if not labels:
            return "I couldn't detect any objects in the image."
        
        formatted_labels = [f"{label['Name']} ({label['Confidence']:.1f}%)" for label in labels]
        return "I see the following in the image:\n" + "\n".join(formatted_labels)
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return "Sorry, I couldn't download the image from the URL."
    except Exception as e:
        print(f"Error analyzing image with Rekognition: {e}")
        return "Sorry, I had a problem analyzing the image."

# QUESTION HANDLER =======================================================================
def handle_question(user_id, question):
    """
    Answer a general question using Amazon Bedrock.
    """
    print(f"Handling question '{question}' for {user_id}")

    # 1. Construct the prompt for the Bedrock model.
    #    This example is for Anthropic Claude 3 Sonnet.
    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}]
            }
        ]
    }

    try:
        # 2. Invoke the model using bedrock_runtime.invoke_model().
        response = bedrock_runtime.invoke_model(
            body=json.dumps(prompt),
            modelId=BEDROCK_MODEL_ID,
            contentType='application/json',
            accept='application/json'
        )

        # 3. Parse the streaming response from Bedrock to get the answer text.
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']

        # 4. Return the answer.
        return answer

    except Exception as e:
        print(f"Error invoking Bedrock model: {e}")
        return "Sorry, I couldn't get an answer for you right now."

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
