"""
Authorization utilities for access control.
"""
import os
from typing import Optional, List
from datetime import datetime

from src.utils.dynamo import DynamoDBClient

class AuthorizationError(Exception):
    """Raised when there is an error during authorization."""
    pass

class Authorization:
    """Authorization utility class."""
    
    def __init__(self, dynamo_client=None, mock_result=None):
        """
        Initialize Authorization utility.
        
        Args:
            dynamo_client: Optional DynamoDB client. If not provided, will create one.
            mock_result: Optional mock result for testing.
        """
        self._dynamo = dynamo_client
        self._mock_result = mock_result
        self._admin_users = None
    
    @property
    def admin_users(self) -> List[str]:
        """Get admin user IDs from SSM parameter."""
        if self._admin_users is None:
            admin_users_param = os.environ.get('ADMIN_USER_IDS', '')
            self._admin_users = [uid.strip() for uid in admin_users_param.split(',') if uid.strip()]
        return self._admin_users
    
    def is_admin(self, user_id: str) -> bool:
        """
        Check if a user is an admin.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user is admin, False otherwise
        """
        return user_id in self.admin_users
    
    @property
    def dynamo(self):
        """Get or create DynamoDB client lazily."""
        if self._dynamo is None:
            self._dynamo = DynamoDBClient(os.environ['FAMILY_FOREST_TABLE_NAME'])
        return self._dynamo
    
    def set_mock_result(self, result: bool) -> None:
        """
        Set mock result for testing.
        
        Args:
            result: True to allow access, False to deny
        """
        self._mock_result = result

    def check_user_authorized(self, user_id: str) -> bool:
        """
        Check if a user is authorized to access their family tree.
        Checks admin status first, then falls back to regular authorization.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if user is authorized, False otherwise
        """
        # Handle mock result first to prevent any interactions in test mode
        if self._mock_result is not None:
            return self._mock_result
            
        # Check admin status first
        if self.is_admin(user_id):
            return True

        try:
            # Only try to use DynamoDB if we have a client
            if not self.dynamo:
                return False

            allowed_user = self.dynamo.get_item({
                "PK": f"USER#{user_id}",
                "SK": "METADATA"
            })
            return bool(allowed_user and allowed_user.get("status") == "active")
        except Exception:
            return False
    
    def add_allowed_user(
        self,
        user_id: str,
        added_by: str,
        tree_name: str = "My Family Tree"
    ) -> None:
        """
        Add a user and create their initial family tree.
        
        Args:
            user_id: Telegram user ID to allow
            added_by: Telegram user ID of admin adding this user
            tree_name: Name for the user's family tree
        """
        self.dynamo.put_item({
            "PK": f"USER#{user_id}",
            "SK": "METADATA",
            "user_id": user_id,
            "tree_name": tree_name,
            "added_by": added_by,
            "added_at": datetime.now().isoformat(),
            "status": "active"
        })
    
    def remove_user(self, user_id: str) -> None:
        """
        Remove a user's access by setting status to inactive.
        
        Args:
            user_id: Telegram user ID to remove
        """
        self.dynamo.update_item(
            key={
                "PK": f"USER#{user_id}",
                "SK": "METADATA"
            },
            update_expression="SET #status = :status",
            expression_values={
                ":status": "inactive"
            }
        )
    
    def verify_tree_access(self, user_id: str, tree_id: str) -> bool:
        """
        Verify that a user has access to view/modify a specific tree.
        Admins have access to all trees, otherwise checks ownership and sharing.
        
        Args:
            user_id: Requesting user's Telegram ID
            tree_id: ID of the family tree
            
        Returns:
            bool: True if user has access to the tree
        """
        # Check admin status first - admins have access to all trees
        if self.is_admin(user_id):
            return True
            
        # For non-admins, verify regular authorization
        if not self.check_user_authorized(user_id):
            return False
            
        tree = self.dynamo.get_item({
            "PK": f"TREE#{tree_id}",
            "SK": "METADATA"
        })
        
        return bool(
            tree and 
            (tree.get("owner_id") == user_id or 
             user_id in tree.get("shared_with", []))
        )
