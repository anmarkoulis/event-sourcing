# System Tests

This directory contains system tests that test the complete application flow from API endpoints to database persistence. Unlike unit tests, these tests use real infrastructure components and a test database.

## What These Tests Do

- **No Mocking**: All infrastructure components (database, event store, etc.) are real
- **Real Database**: Uses a separate test database instance
- **Complete Flow**: Tests the entire request-response cycle
- **Integration Testing**: Verifies that all components work together correctly

## Test Database Setup

The system tests use a separate test database configured via the `TEST_DATABASE_URL` environment variable. The test database is automatically created and cleaned up between test runs.

### Environment Variables

```bash
# Required: Test database connection string
export TEST_DATABASE_URL="postgresql://username:password@host:port/test_database_name"

# Optional: Test environment settings
export ENV="test"
export LOGGING_LEVEL="INFO"
```

### Default Test Database

If `TEST_DATABASE_URL` is not set, the system will use a default test database URL derived from your main `DATABASE_URL` by replacing the database name with "test".

## Running the Tests

### Option 1: Using the Test Runner Script

```bash
# Make the script executable
chmod +x run_system_tests.py

# Run all system tests
./run_system_tests.py
```

### Option 2: Using pytest directly

```bash
# Run all system tests
pytest tests/system/ -v --asyncio-mode=auto

# Run a specific test file
pytest tests/system/test_users.py -v --asyncio-mode=auto

# Run a specific test method
pytest tests/system/test_users.py::TestUserCreation::test_create_user_success -v --asyncio-mode=auto
```

### Option 3: Using pytest with environment variables

```bash
# Set environment and run tests
TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/test_db" \
ENV="test" \
pytest tests/system/ -v --asyncio-mode=auto
```

## Test Structure

### Fixtures

All fixtures are defined in `tests/conftest.py`:

- `test_infrastructure_factory`: Creates infrastructure factory with test database
- `app_with_test_infrastructure`: Overrides app dependencies to use test infrastructure
- `async_client_with_test_db`: HTTP client configured for testing
- `db_engine`: Test database engine with automatic cleanup
- `db`: Database session for each test function

### Test Classes

- `TestUserCreation`: Tests for user creation endpoint (`POST /v1/users/`)

## What Gets Tested

### User Creation Tests

1. **Successful Creation**: Verifies user is created and stored in database
2. **Duplicate Username**: Ensures username uniqueness constraint
3. **Duplicate Email**: Ensures email uniqueness constraint
4. **Invalid Data**: Tests validation of required fields
5. **Business Rules**: Tests username length and password requirements

## Database Cleanup

The test database is automatically cleaned up between test runs:

- Tables are dropped and recreated for each test session
- Each test function runs in a transaction that gets rolled back
- This ensures test isolation and prevents data leakage

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `TEST_DATABASE_URL` is correct
   - Ensure PostgreSQL is running
   - Verify database user has permissions

2. **Tests Hanging**
   - Check for long-running database operations
   - Verify async/await is used correctly
   - Check for unclosed database connections

3. **Test Data Persistence**
   - Tests should be isolated - if data persists, check transaction rollback
   - Verify `db` fixture is working correctly

### Debug Mode

To run tests with more verbose output:

```bash
pytest tests/system/ -v -s --log-cli-level=DEBUG
```

## Adding New System Tests

1. Create test file in `tests/system/`
2. Use the shared fixtures from `tests/conftest.py` for database and HTTP client
3. Test complete user workflows, not just individual components
4. Ensure proper cleanup and isolation
5. Add meaningful assertions that verify business logic
6. **Don't duplicate fixtures** - they're already defined in `conftest.py`

## Performance Considerations

- System tests are slower than unit tests due to real database operations
- Consider running them separately from unit tests in CI/CD
- Use test database connection pooling for better performance
- Monitor test execution time and optimize slow tests
