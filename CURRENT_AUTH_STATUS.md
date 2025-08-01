# Current Authorization Status

## Overview of Existing System

Based on the codebase analysis, here's how authorization currently works in Family Forest:

### Access Control Implementation

Located in `src/utils/auth.py`:
```python
class Authorization:
    def check_user_authorized(self, user_id: str) -> bool:
        """
        Checks if user is authorized to access their family tree.
        Uses DynamoDB to verify user status is "active".
        """
    
    def verify_tree_access(self, user_id: str, tree_id: str) -> bool:
        """
        Verifies if user has access to view/modify a specific tree.
        Access granted if user is either:
        1. The tree owner
        2. Listed in tree's shared_with array
        """
```

### Current Data Model

#### User Authorization Record
```typescript
{
  "PK": "USER#{user_id}",
  "SK": "METADATA",
  "user_id": string,
  "tree_name": string,
  "added_by": string,
  "added_at": timestamp,
  "status": "active" | "inactive"
}
```

#### Family Tree Record
```typescript
{
  "PK": "TREE#{tree_id}",
  "SK": "METADATA",
  "tree_id": string,
  "name": string,
  "description": string,
  "owner_id": string,
  "shared_with": string[],  // Array of user IDs
  "created_at": timestamp,
  "updated_at": timestamp
}
```

## Who Can Currently Access & Modify Data?

### 1. Tree Owners
- Can create and manage their own family trees
- Full control over their tree's data
- Can add/edit/remove family members
- Can share tree with other users

### 2. Shared Users
- Can view and modify trees shared with them
- Same level of access as owners for adding/editing members
- Cannot share the tree with others
- Cannot delete the tree

### 3. Administrators
Currently, there is no explicit admin role. Administrative functions are handled through AWS SSM parameters:
```yaml
# From serverless.yml
environment:
  ADMIN_USER_IDS: ${ssm:/family-forest/admin-users}
```

## Current Authorization Flow

1. **Initial Access**
   ```python
   # When user first interacts with bot
   async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
       user_id = update.effective_user.id
       if not auth.check_user_authorized(user_id):
           # User not authorized
           return
   ```

2. **Tree Creation**
   ```python
   # In TreeService
   def create_tree(self, user_id: str, tree_name: str):
       if not self.auth.check_user_authorized(user_id):
           raise AuthorizationError("User not authorized")
       # Create tree with user as owner
   ```

3. **Tree Access**
   ```python
   # Before any tree operation
   if not self.auth.verify_tree_access(user_id, tree_id):
       raise AuthorizationError("User not authorized for this tree")
   ```

## Current Limitations

1. **Binary Access**
   - Users either have full access or no access
   - No granular permissions
   - Shared users have same privileges as owners

2. **No Role System**
   - Cannot assign different permission levels
   - No way to restrict certain operations

3. **Limited Admin Controls**
   - Admin users defined in SSM parameter
   - No admin interface for user management
   - No audit trail of changes

4. **Basic Sharing**
   - Simple array of shared user IDs
   - No invitation system
   - No way to revoke access easily

## Security Implications

1. **Access Control**
   - Relies on Telegram user IDs for authentication
   - Tree access verified on every operation
   - No session management

2. **Data Protection**
   - All users with access can see all tree data
   - No way to hide sensitive information
   - No encryption of sensitive data

3. **Audit Trail**
   - No logging of who makes changes
   - No way to track access patterns
   - No suspicious activity detection

## Recommended Next Steps

1. Implement the enhanced RBAC system outlined in AUTHORIZATION_PLAN.md
2. Add proper admin interface and controls
3. Implement granular permissions
4. Add audit logging for all changes
5. Create invitation and access management system

See AUTHORIZATION_PLAN.md for detailed implementation plan to address these limitations.
