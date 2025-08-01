"""
Service for managing family trees and their members.
"""
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from aws_lambda_powertools import Logger

from src.models.family_member import FamilyMember
from src.utils.dynamo import DynamoDBClient
from src.utils.auth import Authorization

logger = Logger()

class TreeService:
    """Service for managing family trees."""
    
    def __init__(self, dynamo_client=None):
        """
        Initialize TreeService.
        
        Args:
            dynamo_client: Optional DynamoDB client
        """
        self.dynamo = dynamo_client or DynamoDBClient(
            table_name=os.environ['FAMILY_FOREST_TABLE_NAME']
        )
        self.auth = Authorization(dynamo_client=self.dynamo)
    
    def create_tree(
        self,
        user_id: str,
        tree_name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new family tree.
        
        Args:
            user_id: ID of the user creating the tree
            tree_name: Name of the family tree
            description: Optional description of the tree
            
        Returns:
            Dict containing the created tree info
        """
        if not self.auth.check_user_authorized(user_id):
            logger.warning(f"Unauthorized tree creation attempt: {user_id}")
            raise AuthorizationError("User not authorized")
            
        tree_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        tree_data = {
            "PK": f"TREE#{tree_id}",
            "SK": "METADATA",
            "tree_id": tree_id,
            "name": tree_name,
            "description": description,
            "owner_id": user_id,
            "shared_with": [],
            "created_at": created_at,
            "updated_at": created_at
        }
        
        self.dynamo.put_item(tree_data)
        logger.info(
            "Created new family tree",
            extra={
                "user_id": user_id,
                "tree_id": tree_id
            }
        )
        
        return tree_data
    
    def add_member(
        self,
        user_id: str,
        tree_id: str,
        member_data: Dict[str, Any]
    ) -> FamilyMember:
        """
        Add a new member to a family tree.
        
        Args:
            user_id: ID of the user adding the member
            tree_id: ID of the tree to add member to
            member_data: Dictionary containing member information
            
        Returns:
            Created FamilyMember instance
        """
        if not self.auth.verify_tree_access(user_id, tree_id):
            logger.warning(
                f"Unauthorized member addition attempt",
                extra={
                    "user_id": user_id,
                    "tree_id": tree_id
                }
            )
            raise AuthorizationError("User not authorized for this tree")
            
        member = FamilyMember(
            id=str(uuid.uuid4()),
            name=member_data["name"],
            birth_date=member_data.get("birth_date"),
            death_date=member_data.get("death_date"),
            gender=member_data.get("gender"),
            metadata=member_data.get("metadata", {})
        )
        
        self.dynamo.put_item(member.to_dynamo(tree_id))
        logger.info(
            "Added new family member",
            extra={
                "tree_id": tree_id,
                "member_id": member.id
            }
        )
        
        return member
    
    def get_member(
        self,
        user_id: str,
        tree_id: str,
        member_id: str
    ) -> Optional[FamilyMember]:
        """
        Get a family member from a tree.
        
        Args:
            user_id: ID of the requesting user
            tree_id: ID of the tree
            member_id: ID of the member to get
            
        Returns:
            FamilyMember instance if found, None otherwise
        """
        if not self.auth.verify_tree_access(user_id, tree_id):
            logger.warning(
                f"Unauthorized member access attempt",
                extra={
                    "user_id": user_id,
                    "tree_id": tree_id,
                    "member_id": member_id
                }
            )
            raise AuthorizationError("User not authorized for this tree")
            
        item = self.dynamo.get_item({
            "PK": f"TREE#{tree_id}",
            "SK": f"MEMBER#{member_id}"
        })
        
        return FamilyMember.from_dynamo(item) if item else None
    
    def update_member(
        self,
        user_id: str,
        tree_id: str,
        member_id: str,
        updates: Dict[str, Any]
    ) -> Optional[FamilyMember]:
        """
        Update a family member's information.
        
        Args:
            user_id: ID of the requesting user
            tree_id: ID of the tree
            member_id: ID of the member to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated FamilyMember instance if successful
        """
        member = self.get_member(user_id, tree_id, member_id)
        if not member:
            return None
            
        # Update fields
        for field, value in updates.items():
            if hasattr(member, field):
                setattr(member, field, value)
                
        member.updated_at = datetime.now().isoformat()
        self.dynamo.put_item(member.to_dynamo(tree_id))
        
        logger.info(
            "Updated family member",
            extra={
                "tree_id": tree_id,
                "member_id": member_id,
                "fields_updated": list(updates.keys())
            }
        )
        
        return member
    
    def add_relationship(
        self,
        user_id: str,
        tree_id: str,
        member_id: str,
        related_to: str,
        relationship: str
    ) -> bool:
        """
        Add a relationship between two family members.
        
        Args:
            user_id: ID of the requesting user
            tree_id: ID of the tree
            member_id: ID of the first member
            related_to: ID of the second member
            relationship: Type of relationship
            
        Returns:
            bool indicating success
        """
        member = self.get_member(user_id, tree_id, member_id)
        related = self.get_member(user_id, tree_id, related_to)
        
        if not member or not related:
            return False
            
        # Add relationship in both directions
        member.add_relationship(related_to, relationship)
        self.dynamo.put_item(member.to_dynamo(tree_id))
        
        # Add inverse relationship
        inverse = {
            "parent": "child",
            "child": "parent",
            "spouse": "spouse",
            "sibling": "sibling"
        }.get(relationship, "related")
        
        related.add_relationship(member_id, inverse)
        self.dynamo.put_item(related.to_dynamo(tree_id))
        
        logger.info(
            "Added relationship between members",
            extra={
                "tree_id": tree_id,
                "member_1": member_id,
                "member_2": related_to,
                "relationship": relationship
            }
        )
        
        return True
    
    def get_tree_members(
        self,
        user_id: str,
        tree_id: str
    ) -> List[FamilyMember]:
        """
        Get all members of a family tree.
        
        Args:
            user_id: ID of the requesting user
            tree_id: ID of the tree
            
        Returns:
            List of FamilyMember instances
        """
        if not self.auth.verify_tree_access(user_id, tree_id):
            logger.warning(
                f"Unauthorized tree access attempt",
                extra={
                    "user_id": user_id,
                    "tree_id": tree_id
                }
            )
            raise AuthorizationError("User not authorized for this tree")
            
        items = self.dynamo.query(
            key_condition="PK = :pk AND begins_with(SK, :prefix)",
            expression_values={
                ":pk": f"TREE#{tree_id}",
                ":prefix": "MEMBER#"
            }
        )
        
        return [FamilyMember.from_dynamo(item) for item in items]
    
    def share_tree(
        self,
        user_id: str,
        tree_id: str,
        share_with: str
    ) -> bool:
        """
        Share a family tree with another user.
        
        Args:
            user_id: ID of the sharing user
            tree_id: ID of the tree to share
            share_with: ID of user to share with
            
        Returns:
            bool indicating success
        """
        tree = self.dynamo.get_item({
            "PK": f"TREE#{tree_id}",
            "SK": "METADATA"
        })
        
        if not tree or tree.get("owner_id") != user_id:
            logger.warning(
                f"Unauthorized tree sharing attempt",
                extra={
                    "user_id": user_id,
                    "tree_id": tree_id
                }
            )
            return False
            
        shared_with = set(tree.get("shared_with", []))
        shared_with.add(share_with)
        
        self.dynamo.update_item(
            key={
                "PK": f"TREE#{tree_id}",
                "SK": "METADATA"
            },
            update_expression="SET shared_with = :users",
            expression_values={
                ":users": list(shared_with)
            }
        )
        
        logger.info(
            "Shared tree with user",
            extra={
                "tree_id": tree_id,
                "shared_with": share_with
            }
        )
        
        return True
