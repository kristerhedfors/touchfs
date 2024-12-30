# Simple API Example

This example demonstrates using llmfs to generate a simple Python web API and its client. The filesystem will generate a Flask-based REST API for managing tasks, along with a curl-based client script.

## Usage

```python
# Setup workspace
rm -rf workspace
mkdir workspace
llmfs_mount workspace --prompt "Create a Flask-based REST API for managing tasks"
cd workspace

# Generate API components in sequence
touch README.md        # Describes API structure and endpoints
touch app.py          # AI generates Flask API based on README
touch curl_client.sh  # AI creates client script matching API endpoints

# Cleanup
cd ..
rm -rf workspace
```

## Generated Components

### app.py
A Flask-based REST API that provides:
- GET /tasks - List all tasks
- GET /tasks/{id} - Get a specific task
- POST /tasks - Create a new task
- PUT /tasks/{id} - Update a task
- DELETE /tasks/{id} - Delete a task

### curl_client.sh
A shell script containing curl commands to test each API endpoint:
```bash
# Example usage
./curl_client.sh list     # List all tasks
./curl_client.sh get 1    # Get task with id 1
./curl_client.sh create   # Create a new task
./curl_client.sh update 1 # Update task with id 1
./curl_client.sh delete 1 # Delete task with id 1
```

## Data Model

Each task has the following structure:
```json
{
    "id": 1,
    "title": "Example task",
    "done": false
}
