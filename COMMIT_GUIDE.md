# Commit Message Guidelines

## Commit Structure

Each commit message should follow this format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type
Must be one of the following:
- **feat**: A new feature
- **fix**: A bug fix
- **refactor**: Code changes that neither fix a bug nor add a feature
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (white-space, formatting, etc)
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to build process or auxiliary tools

### Scope
Optional, describes what part of the codebase is affected:
- **auth**: Authentication-related changes
- **tree**: Family tree functionality
- **member**: Family member operations
- **telegram**: Telegram bot functionality
- **utils**: Utility functions
- **deps**: Dependency updates

### Subject
- Use imperative, present tense ("add" not "added" or "adds")
- Don't capitalize first letter
- No period at the end
- Maximum 50 characters

### Body
- Optional
- Use imperative, present tense
- Include motivation for change and contrast with previous behavior
- Wrap at 72 characters

### Footer
- Optional
- Reference issues being closed: "Closes #123"
- Breaking changes should start with "BREAKING CHANGE:"

## Examples

```
feat(member): add family member creation functionality

Implement core functionality to add new family members with basic
information and relationships.

Closes #45
```

```
fix(telegram): handle rate limit errors properly

Add proper handling of 429 responses from Telegram API to implement
exponential backoff and retry logic.
```

```
refactor(utils): extract relationship validation functions

Move relationship validation logic to separate module to improve
code organization and reusability.
```

## Git Workflow

1. **Branch naming**
   - `feature/description`: New features
   - `fix/description`: Bug fixes
   - `refactor/description`: Code restructuring
   - `docs/description`: Documentation updates

2. **Before committing**
   - Run tests: `npm test`
   - Run linter: `npm run lint`
   - Ensure no debugging code is left
   - Check for sensitive data

3. **Pull Request process**
   - Create branch from main
   - Make changes in small, logical commits
   - Update tests and documentation
   - Create PR with clear description
   - Request review from team members

## Pre-commit Checklist

- [ ] Tests pass
- [ ] Code is linted
- [ ] No debugging code
- [ ] No sensitive data
- [ ] Documentation updated
- [ ] Commit message follows guidelines
- [ ] Changes are atomic
- [ ] Branch is up to date
