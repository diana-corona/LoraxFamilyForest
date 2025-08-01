"""
Family member data model.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List

@dataclass
class FamilyMember:
    """
    Represents a family member in the family tree.
    """
    id: str
    name: str
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    gender: Optional[str] = None
    relationships: Dict[str, str] = None  # member_id: relationship_type
    metadata: Dict[str, str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.relationships is None:
            self.relationships = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dynamo(self, tree_id: str) -> Dict:
        """
        Convert the member to a DynamoDB item.
        
        Args:
            tree_id: ID of the family tree this member belongs to
            
        Returns:
            Dict representing the DynamoDB item
        """
        return {
            "PK": f"TREE#{tree_id}",
            "SK": f"MEMBER#{self.id}",
            "member_id": self.id,
            "name": self.name,
            "birth_date": self.birth_date,
            "death_date": self.death_date,
            "gender": self.gender,
            "relationships": self.relationships,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dynamo(cls, item: Dict) -> 'FamilyMember':
        """
        Create a FamilyMember instance from a DynamoDB item.
        
        Args:
            item: DynamoDB item
            
        Returns:
            FamilyMember instance
        """
        return cls(
            id=item["member_id"],
            name=item["name"],
            birth_date=item.get("birth_date"),
            death_date=item.get("death_date"),
            gender=item.get("gender"),
            relationships=item.get("relationships", {}),
            metadata=item.get("metadata", {}),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at")
        )
    
    def add_relationship(self, member_id: str, relationship: str) -> None:
        """
        Add or update a relationship with another member.
        
        Args:
            member_id: ID of the related member
            relationship: Type of relationship (e.g., "parent", "child", "spouse")
        """
        self.relationships[member_id] = relationship
        self.updated_at = datetime.now().isoformat()
    
    def remove_relationship(self, member_id: str) -> None:
        """
        Remove a relationship with another member.
        
        Args:
            member_id: ID of the member to remove relationship with
        """
        if member_id in self.relationships:
            del self.relationships[member_id]
            self.updated_at = datetime.now().isoformat()
    
    def get_relationships_by_type(self, relationship_type: str) -> List[str]:
        """
        Get all member IDs with a specific relationship type.
        
        Args:
            relationship_type: Type of relationship to filter by
            
        Returns:
            List of member IDs with the specified relationship
        """
        return [
            member_id
            for member_id, rel_type in self.relationships.items()
            if rel_type == relationship_type
        ]
