# Contributing Guidelines

## Code Organization

When adding new functionality to the codebase, follow these guidelines to maintain clean and maintainable code:

### 1. Module Structure

- Place code in the appropriate module based on its responsibility:
  - `src/handlers/` - Command and event handlers
  - `src/models/` - Data models and schemas
  - `src/services/` - Business logic and core functionality
  - `src/utils/` - Utility functions and helpers

### 2. Single Responsibility Principle

- Each module should have a single, well-defined purpose
- If a module grows too large or handles multiple concerns, split it into smaller modules
- Example: Telegram utilities are split into:
  - `formatters.py` - Message formatting only
  - `keyboards.py` - Keyboard creation only
  - `parsers.py` - Command parsing only
  - `validators.py` - Data validation only

### 3. New Feature Checklist

When adding a new feature:

1. **Identify the Responsibility**
   - What is the core purpose of this feature?
   - Which existing module category does it belong to?

2. **Choose Module Location**
   - Create a new module if it's a distinct responsibility
   - Add to existing module if it's closely related functionality
   - Consider creating a new package if it's a large feature with multiple components

3. **Code Structure**
   - Start with interfaces and models
   - Implement core logic in services
   - Add handlers for user interaction
   - Create utility functions only for reusable code

### 4. Testing

- Create unit tests for new functionality
- Test files should mirror the structure of source files
- Example: `test_tree_service.py` tests `tree_service.py`

### 5. Code Guidelines

- Follow existing code style (use a linter)
- Keep functions focused and small
- Use descriptive names for functions and variables
- Add type hints to function parameters and returns
- Document complex logic with comments

### 6. Docstring Documentation

Python docstrings should follow Google's style:

```python
def add_family_member(user_id: str, member_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new family member to the user's family tree.

    Args:
        user_id: The unique identifier of the user
        member_data: Dictionary containing member information:
            - name (str): Full name of the member
            - birth_date (str): Date of birth (YYYY-MM-DD)
            - relationship (str): Relationship to user

    Returns:
        Dict containing the created member:
        {
            "member_id": str,
            "created_at": datetime,
            "member_data": Dict
        }

    Raises:
        ValidationError: If member data is invalid
        AuthorizationError: If user is not authorized
    """
```

### 7. Error Handling
-  **Centralized Authorization**: All authorization is handled by the main webhook handler (`src/handlers/telegram/handler.py`):
  ```python
  # Authorization is centralized in the handler for ALL interactions
  # including both regular messages and callback queries (button clicks)
  if not auth.check_user_authorized(user_id):
      logger.warning("Unauthorized access attempt")
      return silent_success_response()
  ```
  - Do NOT add authorization checks in individual command handlers
  - Do NOT use the @require_auth decorator (it's redundant)
  - All user interactions (messages, buttons, etc.) are authorized at entry
  - This prevents security holes and unauthorized access attempts

- Use specific exception types:
```python
class MemberNotFoundError(Exception):
    """Raised when a family member is not found."""
    pass

class RelationshipError(Exception):
    """Raised when there's an invalid relationship operation."""
    pass
```

- Structure error handling consistently:
```python
def process_member_data(user_id: str, member_id: str) -> Dict[str, Any]:
    try:
        member = get_member(user_id, member_id)
        if not member:
            raise MemberNotFoundError(f"Member {member_id} not found")
        
        processed_data = process_data(member)
        return processed_data
        
    except MemberNotFoundError as e:
        logger.warning(str(e), extra={"user_id": user_id})
        raise
        
    except Exception as e:
        logger.exception("Unexpected error", extra={
            "user_id": user_id,
            "error_type": e.__class__.__name__
        })
        raise
```

### 8. Logging Guidelines

- Use the aws_lambda_powertools Logger
- Log at appropriate levels:
  - ERROR - Errors that affect functionality
  - WARNING - Unexpected but handled cases
  - INFO - Normal operational events
  - DEBUG - Detailed information for debugging

- Include contextual information:
```python
logger.info("Processing family member", extra={
    "user_id": user_id,
    "member_id": member_id,
    "action": action
})
```

### 9. Security Guidelines

- Never expose sensitive family information
- Validate all relationship changes
- Log security events appropriately
- Handle authorization failures silently
- Keep family trees private to authorized users only

### 10. Code Organization Example

```
src/
└── family_tree/
    ├── __init__.py
    ├── models.py       # Data models
    ├── handlers.py     # Request handlers
    ├── services.py     # Business logic
    └── utils/          # Tree-specific utilities
        ├── __init__.py
        └── validators.py
```

### 11. Import Organization

```python
# Standard library
from typing import Dict, Any
from datetime import datetime

# Third-party
from aws_lambda_powertools import Logger

# Local
from src.models.member import FamilyMember
from src.utils.validators import validate_relationship
```

Following these guidelines helps maintain code quality and makes the codebase easier to understand and modify in the future.
