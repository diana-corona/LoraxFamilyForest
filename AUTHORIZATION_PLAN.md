# Family Forest Authorization System

This document outlines the enhanced authorization system for Family Forest, supporting collaborative family tree management with fine-grained permissions and secure sharing.

## Current System Analysis

### Existing Features
- Basic user authorization via `check_user_authorized`
- Tree ownership with `owner_id`
- Simple sharing via `shared_with` array
- Access verification through `verify_tree_access`

### Limitations
- Binary access control (owner vs shared)
- No granular permissions
- Limited collaboration features
- Basic sharing mechanism

## Enhanced Authorization System

### Role-Based Access Control (RBAC)

#### Roles and Permissions
1. **Owner**
   - Full control over tree
   - Can delete tree
   - Can manage all permissions
   - Can transfer ownership

2. **Admin**
   - Add/edit all members
   - Manage relationships
   - Invite new users
   - Modify tree settings
   - Cannot delete tree or transfer ownership

3. **Editor**
   - Add/edit family members
   - Create/modify relationships
   - Upload media
   - Cannot manage permissions or settings

4. **Viewer**
   - View tree and members
   - View relationships
   - View media
   - Read-only access

### Database Schema

#### Permissions Table
```typescript
interface TreePermission {
  PK: string;          // TREE#{tree_id}#PERMISSIONS#{user_id}
  SK: string;          // METADATA
  user_id: string;     // Telegram user ID
  tree_id: string;     // Associated tree ID
  role: Role;          // owner | admin | editor | viewer
  granted_by: string;  // User ID who granted permission
  granted_at: string;  // ISO timestamp
  permissions: {
    add_members: boolean;
    edit_members: boolean;
    manage_relationships: boolean;
    invite_users: boolean;
    manage_media: boolean;
    manage_permissions: boolean;
    export_tree: boolean;
  };
  metadata: {
    last_accessed: string;
    access_count: number;
  };
}
```

#### Invitations Table
```typescript
interface TreeInvitation {
  PK: string;          // TREE#{tree_id}#INVITATIONS#{invitation_id}
  SK: string;          // METADATA
  invitation_id: string;
  tree_id: string;
  invited_by: string;  // User ID who created invitation
  invited_user: string;// Target user ID/email/phone
  role: Role;          // Proposed role
  status: string;      // pending | accepted | declined | expired
  created_at: string;  // ISO timestamp
  expires_at: string;  // ISO timestamp
  metadata: {
    message: string;   // Optional invitation message
    notification_sent: boolean;
  };
}
```

### Implementation

#### Enhanced Authorization Service
```python
class TreePermissions:
    """Enhanced permission management for family trees."""
    
    def __init__(self, dynamo_client=None):
        self.dynamo = dynamo_client or DynamoDBClient(
            table_name=os.environ['FAMILY_FOREST_TABLE_NAME']
        )
    
    def get_user_permissions(
        self,
        user_id: str,
        tree_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's permissions for a tree."""
        return self.dynamo.get_item({
            "PK": f"TREE#{tree_id}#PERMISSIONS#{user_id}",
            "SK": "METADATA"
        })
    
    def check_permission(
        self,
        user_id: str,
        tree_id: str,
        permission: str
    ) -> bool:
        """Check if user has specific permission."""
        perms = self.get_user_permissions(user_id, tree_id)
        if not perms:
            return False
            
        # Owner has all permissions
        if perms["role"] == "owner":
            return True
            
        return perms["permissions"].get(permission, False)
    
    def grant_permission(
        self,
        granter_id: str,
        tree_id: str,
        grantee_id: str,
        role: str,
        custom_permissions: Optional[Dict[str, bool]] = None
    ) -> bool:
        """Grant permissions to a user."""
        # Verify granter has permission to grant
        if not self.check_permission(granter_id, tree_id, "manage_permissions"):
            return False
            
        permissions = self._get_role_permissions(role)
        if custom_permissions:
            permissions.update(custom_permissions)
            
        self.dynamo.put_item({
            "PK": f"TREE#{tree_id}#PERMISSIONS#{grantee_id}",
            "SK": "METADATA",
            "user_id": grantee_id,
            "tree_id": tree_id,
            "role": role,
            "granted_by": granter_id,
            "granted_at": datetime.now().isoformat(),
            "permissions": permissions
        })
        
        return True
```

#### Invitation System
```python
class TreeInvitations:
    """Manage invitations to family trees."""
    
    def create_invitation(
        self,
        tree_id: str,
        inviter_id: str,
        invited_user: str,
        role: str,
        expires_in_days: int = 7
    ) -> Optional[str]:
        """Create a new invitation."""
        if not permissions.check_permission(inviter_id, tree_id, "invite_users"):
            return None
            
        invitation_id = str(uuid.uuid4())
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=expires_in_days)
        
        self.dynamo.put_item({
            "PK": f"TREE#{tree_id}#INVITATIONS#{invitation_id}",
            "SK": "METADATA",
            "invitation_id": invitation_id,
            "tree_id": tree_id,
            "invited_by": inviter_id,
            "invited_user": invited_user,
            "role": role,
            "status": "pending",
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat()
        })
        
        return invitation_id
    
    def accept_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> bool:
        """Accept a pending invitation."""
        invitation = self._get_invitation(invitation_id)
        if not invitation or invitation["status"] != "pending":
            return False
            
        if (invitation["invited_user"] != user_id or
            datetime.fromisoformat(invitation["expires_at"]) < datetime.now()):
            return False
            
        # Grant permissions
        success = permissions.grant_permission(
            invitation["invited_by"],
            invitation["tree_id"],
            user_id,
            invitation["role"]
        )
        
        if success:
            self._update_invitation_status(invitation_id, "accepted")
            
        return success
```

### Security Features

#### 1. Activity Logging
```python
class TreeActivityLog:
    """Log tree-related activities for audit purposes."""
    
    def log_activity(
        self,
        tree_id: str,
        user_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Log an activity."""
        self.dynamo.put_item({
            "PK": f"TREE#{tree_id}#ACTIVITY",
            "SK": f"{datetime.now().isoformat()}#{str(uuid.uuid4())}",
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
```

#### 2. Rate Limiting
```python
class InvitationRateLimiter:
    """Rate limit invitation creation."""
    
    def check_rate_limit(
        self,
        user_id: str,
        tree_id: str
    ) -> bool:
        """Check if user has exceeded invitation rate limit."""
        recent_invites = self._count_recent_invitations(user_id, tree_id)
        return recent_invites < MAX_INVITES_PER_DAY
```

### Mini App Integration

#### Permission-Aware Components
```typescript
interface TreeViewProps {
  treeId: string;
  userId: string;
  permissions: TreePermission;
}

const TreeView: React.FC<TreeViewProps> = ({ treeId, userId, permissions }) => {
  return (
    <div className="tree-view">
      <TreeVisualization
        treeId={treeId}
        isEditable={permissions.permissions.manage_relationships}
      />
      
      {permissions.permissions.add_members && (
        <AddMemberButton onClick={handleAddMember} />
      )}
      
      {permissions.role === "owner" && (
        <ManagePermissionsPanel treeId={treeId} />
      )}
    </div>
  );
};
```

#### Permission Management UI
```typescript
const PermissionManagement: React.FC<{ treeId: string }> = ({ treeId }) => {
  const [users, setUsers] = useState<TreeUser[]>([]);
  
  const handleRoleChange = async (userId: string, newRole: Role) => {
    try {
      await api.updateUserRole(treeId, userId, newRole);
      // Update local state
    } catch (error) {
      // Handle error
    }
  };
  
  return (
    <div className="permission-management">
      <h2>Manage Access</h2>
      <UserList
        users={users}
        onRoleChange={handleRoleChange}
        onRemoveUser={handleRemoveUser}
      />
      <InviteUserForm onInvite={handleInvite} />
    </div>
  );
};
```

## Implementation Timeline

### Phase 1: Core RBAC (Weeks 1-2)
- [ ] Enhanced permission schema
- [ ] Basic role implementation
- [ ] Permission checking service
- [ ] Activity logging

### Phase 2: Invitation System (Weeks 3-4)
- [ ] Invitation database schema
- [ ] Invitation creation and management
- [ ] Notification system
- [ ] Rate limiting

### Phase 3: UI Integration (Weeks 5-6)
- [ ] Permission-aware components
- [ ] Permission management interface
- [ ] Invitation management UI
- [ ] Activity log viewer

### Phase 4: Advanced Features (Weeks 7-8)
- [ ] Custom role creation
- [ ] Bulk permission management
- [ ] Permission inheritance
- [ ] Advanced activity analytics

## Testing Strategy

### Unit Tests
```python
def test_permission_grant():
    """Test granting permissions to users."""
    perms = TreePermissions(mock_dynamo)
    
    # Test granting as owner
    assert perms.grant_permission(
        "owner_id",
        "tree_id",
        "new_user",
        "editor"
    ) == True
    
    # Test granting without permission
    assert perms.grant_permission(
        "viewer_id",
        "tree_id",
        "new_user",
        "editor"
    ) == False
```

### Integration Tests
```python
def test_invitation_workflow():
    """Test complete invitation workflow."""
    invites = TreeInvitations(mock_dynamo)
    perms = TreePermissions(mock_dynamo)
    
    # Create invitation
    inv_id = invites.create_invitation(
        "tree_id",
        "owner_id",
        "new_user",
        "editor"
    )
    assert inv_id is not None
    
    # Accept invitation
    assert invites.accept_invitation(inv_id, "new_user") == True
    
    # Verify permissions
    assert perms.check_permission(
        "new_user",
        "tree_id",
        "edit_members"
    ) == True
```

## Security Considerations

### Access Control
- Validate all permission changes
- Prevent privilege escalation
- Maintain permission audit logs
- Regular permission reviews

### Invitation Security
- Secure invitation tokens
- Limited invitation validity
- Rate limiting
- Notification on permission changes

### Data Protection
- Role-based data access
- Encrypted sensitive data
- Audit logging
- Backup and recovery

## Future Enhancements

### 1. Advanced Collaboration
- Real-time editing notifications
- Conflict resolution
- Change requests/approvals
- Comment system

### 2. Smart Permissions
- AI-based suspicious activity detection
- Automated role suggestions
- Dynamic permission adjustment
- Usage analytics

### 3. Enhanced Privacy
- Private branches
- Selective sharing
- Data export controls
- Privacy impact analysis

## Conclusion

This enhanced authorization system provides a robust foundation for collaborative family tree management while maintaining security and privacy. Regular reviews and updates should be conducted to ensure it continues to meet user needs and security requirements.
