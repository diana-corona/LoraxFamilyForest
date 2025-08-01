"""
DynamoDB client utility for database operations.
"""
from typing import Dict, Any, Optional, List

import boto3
from aws_lambda_powertools import Logger

logger = Logger()

class DynamoDBClient:
    """Client for interacting with DynamoDB."""
    
    def __init__(self, table_name: str):
        """
        Initialize DynamoDB client.
        
        Args:
            table_name: Name of the DynamoDB table
        """
        self.table_name = table_name
        self.dynamo = boto3.resource('dynamodb')
        self.table = self.dynamo.Table(table_name)
    
    def get_item(self, key: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB.
        
        Args:
            key: Key of the item to get
            
        Returns:
            Dict containing the item if found, None otherwise
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except Exception as e:
            logger.error(
                "Error getting item from DynamoDB",
                extra={
                    "table": self.table_name,
                    "key": key,
                    "error": str(e)
                }
            )
            return None
    
    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Put an item in DynamoDB.
        
        Args:
            item: Item to put in the table
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            logger.error(
                "Error putting item in DynamoDB",
                extra={
                    "table": self.table_name,
                    "item": item,
                    "error": str(e)
                }
            )
            return False
    
    def update_item(
        self,
        key: Dict[str, str],
        update_expression: str,
        expression_values: Dict[str, Any]
    ) -> bool:
        """
        Update an item in DynamoDB.
        
        Args:
            key: Key of the item to update
            update_expression: Update expression (e.g., "SET #status = :status")
            expression_values: Values for the update expression
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames={
                    '#' + k: k 
                    for k in [x.strip('#') for x in update_expression.split() if x.startswith('#')]
                },
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception as e:
            logger.error(
                "Error updating item in DynamoDB",
                extra={
                    "table": self.table_name,
                    "key": key,
                    "error": str(e)
                }
            )
            return False
    
    def query(
        self,
        key_condition: str,
        expression_values: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Query items from DynamoDB.
        
        Args:
            key_condition: Key condition expression
            expression_values: Values for the key condition
            
        Returns:
            List of items matching the query
        """
        try:
            response = self.table.query(
                KeyConditionExpression=key_condition,
                ExpressionAttributeNames={
                    '#' + k: k 
                    for k in [x.strip('#') for x in key_condition.split() if x.startswith('#')]
                },
                ExpressionAttributeValues=expression_values
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(
                "Error querying DynamoDB",
                extra={
                    "table": self.table_name,
                    "condition": key_condition,
                    "error": str(e)
                }
            )
            return []
    
    def delete_item(self, key: Dict[str, str]) -> bool:
        """
        Delete an item from DynamoDB.
        
        Args:
            key: Key of the item to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.delete_item(Key=key)
            return True
        except Exception as e:
            logger.error(
                "Error deleting item from DynamoDB",
                extra={
                    "table": self.table_name,
                    "key": key,
                    "error": str(e)
                }
            )
            return False
