import unittest
import boto3
import os
import sys
from moto import mock_aws

# This is a common trick to make sure the test file can find the lambda_function code
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from lambda_function.main import handle_todo_list, todo_table

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
        # self.assertNotIn('buy milk', updated_item['TodoList'])
        
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
        
if __name__ == '__main__':
    unittest.main()