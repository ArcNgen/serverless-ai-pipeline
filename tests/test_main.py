import unittest
import boto3
import os
import sys
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock

# This is a common trick to make sure the test file can find the lambda_function code
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from lambda_function.main import handle_todo_list, todo_table, handle_question, handle_image_analysis

# The @mock_aws decorator intercepts any boto3 calls and redirects them to the mock environment
@mock_aws
class TestTodoListHandler(unittest.TestCase):
    
    def setUp(self):
        """
        This method is called before each test.
        It sets up the mock DynamoDB table and pre-loads it with some data.
        """
        # 1. Define the schema for our mock table
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.dynamodb.create_table(
            TableName='AI-Assistant-Users',
            KeySchema=[{'AttributeName': 'UserID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'UserID', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        # 2. Connect our main code's table object to the mock table
        # This is a crucial step to ensure the function-under-test uses the mock table
        global todo_table
        todo_table = self.dynamodb.Table('AI-Assistant-Users')
        
        # 3. Add a test user with an existing todo list
        self.test_user_id = '+15551234567'
        todo_table.put_item(Item={
            'UserID': self.test_user_id,
            'TodoList': ['buy milk', 'walk the dog']
        })
        
    def test_add_item_to_existing_list(self):
        """Tests adding a new item to a user's list."""
        command = "add finish the project"
        response = handle_todo_list(self.test_user_id, command)
        
        self.assertIn("Added 'finish the project'", response)
        
        # Verify the item was actually added in DynamoDB
        updated_item = todo_table.get_item(Key={'UserID': self.test_user_id})['Item']
        self.assertEqual(len(updated_item['TodoList']), 3)
        self.assertIn('finish the project', updated_item['TodoList'])
        
    def test_add_item_to_new_user(self):
        """Tests that a new user can add their first item."""
        new_user_id = '+15557654321'
        command = "add start a new list"
        response = handle_todo_list(new_user_id, command)
        
        self.assertIn("Added 'start a new list'", response)
        
        # Verify the new user and their list were created
        new_item = todo_table.get_item(Key={'UserID': new_user_id})['Item']
        self.assertEqual(len(new_item['TodoList']), 1)
        self.assertEqual(new_item['TodoList'][0], 'start a new list')
        
    def test_list_items(self):
        """Tests the 'list' command."""
        command = "list"
        response = handle_todo_list(self.test_user_id, command)
        
        self.assertIn("1. buy milk", response)
        self.assertIn("2. walk the dog", response)
        
    def test_remove_item(self):
        """Tests removing an item by its number."""
        command = "remove 2"
        response = handle_todo_list(self.test_user_id, command)
        
        self.assertIn("Removed 'walk the dog'", response)
        
        # Verify the item was actually removed in DynamoDB
        updated_item = todo_table.get_item(Key={'UserID': self.test_user_id})['Item']
        self.assertEqual(len(updated_item['TodoList']), 1)
        self.assertEqual(updated_item['TodoList'][0], 'buy milk')
        
    def test_remove_invalid_number(self):
        """Tests removing an item with an invalid number."""
        command = "remove 99"
        response = handle_todo_list(self.test_user_id, command)
        
        self.assertIn("not a valid number", response)
        
    def tearDown(self):
        """
        This method is called after each test.
        It cleans up the mock table.
        """
        # Delete the mock table
        self.dynamodb.Table('AI-Assistant-Users').delete()

class TestQuestionHandler(unittest.TestCase):

    @patch('lambda_function.main.bedrock_runtime')
    def test_handle_question_success(self, mock_bedrock_runtime):
        """Tests the question handler with a successful Bedrock API call."""
        # 1. Setup the mock response from Bedrock
        # HINT: Create a dictionary that looks like the real API response.
        # The important part is response['body'].read(), which should be a 
        # JSON string with a structure like:
        # {"content": [{"text": "This is the mock answer."}]}
        
        mock_response_body = {"content": [{"text": "This is the mock answer."}]}
        mock_streaming_body = MagicMock()
        mock_streaming_body.read.return_value = json.dumps(mock_response_body)
        
        mock_bedrock_runtime.invoke_model.return_value = {
            'body': mock_streaming_body
        }
        
        # 2. Call the function with a test question
        user_id = '+15559998888'
        question = "What is the capital of France?"
        
        response = handle_question(user_id, question)
        
        # 3. Assert that the function returned the correct answer
        # HINT: The expected answer should be the text from your mock response.
        
        self.assertEqual(response, "This is the mock answer.")
        
        # 4. Assert that the invoke_model method was called correctly
        # HINT: Use mock_bedrock_runtime.invoke_model.assert_called_once()
        
        mock_bedrock_runtime.invoke_model.assert_called_once()

    @patch('lambda_function.main.bedrock_runtime')
    def test_handle_question_error(self, mock_bedrock_runtime):
        """Tests the question handler when the Bedrock API call fails."""
        # 1. Setup the mock to raise an exception when called
        # HINT: Use mock_bedrock_runtime.invoke_model.side_effect = Exception("Bedrock error")
        
        mock_bedrock_runtime.invoke_model.side_effect = Exception("Bedrock error")
        
        # 2. Call the function
        user_id = '+15559998888'
        question = "This will fail"
        response = handle_question(user_id, question)
        
        # 3. Assert that the function returned the user-friendly error message
        self.assertEqual(response, "Sorry, I couldn't get an answer for you right now.")

class TestImageAnalysisHandler(unittest.TestCase):
    
    @patch('lambda_function.main.requests.get')
    @patch('lambda_function.main.rekognition_client')
    def test_handle_image_analysis_success(self, mock_rekognition_client, mock_requests_get):
        
        """Test the image analysis with a successful Rekognition API call."""
        # 1. Mock the image download (requests.get)
        mock_image_content = b'fake-image-bytes'
        mock_response = MagicMock()
        mock_response.content = mock_image_content
        mock_requests_get.return_value = mock_response
        
        # 2. Mock the Rekognition API call
        mock_rekognition_response = {
            'Labels': [
                {'Name': 'Dog', 'Confidence': 95.5},
                {'Name': 'Golden Retriever', 'Confidence': 92.1},
                {'Name': 'Park', 'Confidence': 85.0}
            ]
        }
        mock_rekognition_client.detect_labels.return_value = mock_rekognition_response
        
        # 3. Call the function
        user_id = '+5551112222'
        image_url = 'http://example.com/fake-image.jpg'
        response = handle_image_analysis(user_id, image_url)
        
        # 4. Assert the response is formatted correctly
        self.assertIn("I see the following in the image:", response)
        self.assertIn("Dog (95.5%)", response)
        self.assertIn("Golden Retriever (92.1%)", response)
        self.assertIn("Park (85.0%)", response)


if __name__ == '__main__':
    unittest.main()