# Event Sourcing User Management System

A simple user management system built with Event Sourcing and CQRS patterns using FastAPI and Celery.

## Features

### User Management
- **Create User**: POST `/users/` - Create a new user account
- **Update User**: PUT `/users/{user_id}` - Update user information (first name, last name, email)
- **Change Username**: PUT `/users/{user_id}/username` - Change user's username
- **Change Password**: PUT `/users/{user_id}/password` - Change user's password
- **Delete User**: DELETE `/users/{user_id}` - Delete user account
- **Get User**: GET `/users/{user_id}` - Get user information
- **Get User History**: GET `/users/{user_id}/history` - Get user event history

### Password Reset Flow
- **Request Password Reset**: POST `/users/password-reset/request` - Request password reset email
- **Complete Password Reset**: POST `/users/password-reset/complete` - Complete password reset with token

## Architecture

### Event Sourcing Components

1. **User Aggregate** (`domain/aggregates/user.py`)
   - Contains business logic for user operations
   - Validates business rules
   - Generates domain events

2. **Commands** (`application/commands/user.py`)
   - `CreateUserCommand`
   - `UpdateUserCommand`
   - `ChangeUsernameCommand`
   - `ChangePasswordCommand`
   - `RequestPasswordResetCommand`
   - `CompletePasswordResetCommand`
   - `DeleteUserCommand`

3. **Command Handlers** (`application/commands/handlers/user_handlers.py`)
   - Process commands and interact with aggregates
   - Store events in event store
   - Dispatch events to message queue

4. **Events** (defined in `enums.py`)
   - `USER_CREATED`
   - `USER_UPDATED`
   - `USER_DELETED`
   - `USERNAME_CHANGED`
   - `PASSWORD_CHANGED`
   - `PASSWORD_RESET_REQUESTED`
   - `PASSWORD_RESET_COMPLETED`

5. **Projections** (`application/projections/user_projection.py`)
   - Update read models from events
   - Handle different event types
   - Maintain eventual consistency

6. **Celery Tasks** (`application/tasks/process_user_event.py`)
   - Process events asynchronously
   - Call appropriate projections
   - Handle event processing failures

## API Examples

### Create User
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "secure_password"
  }'
```

### Update User
```bash
curl -X PUT "http://localhost:8000/users/{user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Johnny",
    "last_name": "Smith"
  }'
```

### Change Username
```bash
curl -X PUT "http://localhost:8000/users/{user_id}/username" \
  -H "Content-Type: application/json" \
  -d '{
    "new_username": "johnny_smith"
  }'
```

### Change Password
```bash
curl -X PUT "http://localhost:8000/users/{user_id}/password" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "old_password",
    "new_password": "new_secure_password"
  }'
```

### Request Password Reset
```bash
curl -X POST "http://localhost:8000/users/password-reset/request" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

### Complete Password Reset
```bash
curl -X POST "http://localhost:8000/users/password-reset/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "new_secure_password",
    "reset_token": "reset_token_from_email"
  }'
```

### Delete User
```bash
curl -X DELETE "http://localhost:8000/users/{user_id}"
```

## Business Rules

### User Creation
- Username must be at least 3 characters
- Email must be valid format
- Password is required
- Cannot create user if already exists

### User Updates
- Cannot update deleted user
- Must provide at least one field to update
- Email must be valid if provided

### Username Changes
- Cannot change username for deleted user
- New username must be different from current
- Username must be at least 3 characters

### Password Changes
- Cannot change password for deleted user
- Password is required

### Password Reset
- Cannot request reset for deleted user
- Reset token is required for completion
- Password is required for completion

### User Deletion
- Cannot delete already deleted user

## Event Sourcing Benefits

1. **Complete Audit Trail**: Every user action is recorded as an immutable event
2. **Time Travel**: Can rebuild user state at any point in time
3. **Debugging Superpowers**: Can replay events to understand what happened
4. **Scalability**: Commands and queries are separated (CQRS)
5. **Eventual Consistency**: Read models are updated asynchronously

## Technology Stack

- **FastAPI**: Web framework for API endpoints
- **Celery**: Asynchronous task processing
- **PostgreSQL**: Event store and read model database
- **Pydantic**: Data validation and serialization
- **Event Sourcing**: Architecture pattern for data persistence
- **CQRS**: Command Query Responsibility Segregation

## Getting Started

1. Set up PostgreSQL database
2. Configure environment variables
3. Run database migrations
4. Start FastAPI server
5. Start Celery worker
6. Use the API endpoints

## Future Enhancements

- Add authentication and authorization
- Implement proper password hashing
- Add email service for password reset
- Add user search and filtering
- Implement user snapshots for performance
- Add event replay capabilities
- Add monitoring and metrics
