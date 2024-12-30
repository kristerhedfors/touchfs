This example demonstrates using TouchFS to generate a simple Python web API and its client. The filesystem will generate a Flask-based REST API for managing tasks, along with a curl-based client script.

## Usage

1. Create workspace:
```bash
mkdir workspace
```

2. Mount TouchFS with prompt:
```bash
touchfs_mount workspace --prompt "Create a Flask-based REST API for managing tasks"
```

3. Enter workspace:
```bash
cd workspace
```

4. Generate files:
```bash
# Create README with API specification
touch README.md

# Generate Flask API implementation
touch app.py

# Create curl-based client script
touch curl_client.sh
chmod +x curl_client.sh
```

5. Start the server:
```bash
python app.py
```

6. Test the API:
```bash
# List tasks
./curl_client.sh list

# Create a task
./curl_client.sh create

# Update a task
./curl_client.sh update 1

# Delete a task
./curl_client.sh delete 1
