#!/bin/bash

# Get the first non-loopback IP address of the machine (used for local access URL)
IP=$(hostname -I | awk '{print $1}')

# Set OAKAPP_STATIC_FRONTEND_PORT to 8000 if it's not already defined
export OAKAPP_STATIC_FRONTEND_PORT="${OAKAPP_STATIC_FRONTEND_PORT:-8000}"

# Helper function to extract a specific attribute from the "data" field of a JSON response
get_data_attr() {
    echo "$1" | python3.12 -c "import sys, json; print(json.load(sys.stdin)['data']['$2'])"
}

# Function to fetch a connection token from the agent service
write_connection() {
    while true; do
        # Log current values for debugging
        # echo "CONNECTION - IP: $IP"
        # echo "CONNECTION - OAKAPP_STATIC_FRONTEND_PORT: $OAKAPP_STATIC_FRONTEND_PORT"
        # echo "CONNECTION - OAKAGENT_APP_VERSION: $OAKAGENT_APP_VERSION"
        # echo "CONNECTION - OAKAGENT_CONTAINER_ID: $OAKAGENT_CONTAINER_ID"

        # Check that required credentials are present
        if [[ -n "$OAKAGENT_PRIVATE_HTTP_PWD" && -n "$OAKAGENT_CONTAINER_ID" ]]; then
            # Perform request to agent to get connection info, storing response and status separately
            CONNECTION=$(curl -s -w "%{http_code}" -o /tmp/connection_respons.json \
                -H "Authorization: $OAKAGENT_PRIVATE_HTTP_PWD" \
                -d "app_id=$OAKAGENT_CONTAINER_ID" \
                -X GET http://127.0.0.1:9091/get-connection)
            CONNECTION_RESPONSE=$(cat /tmp/connection_respons.json)
            rm /tmp/connection_respons.json

            # Check if the request failed (non-200 response)
            if [[ "$CONNECTION" != "200" ]]; then
                echo "CONNECTION - Agent request failed with status $CONNECTION"
                # cat /tmp/connection_respons.json | jq .
            else
                echo "CONNECTION - Agent request succeeded"
                # cat /tmp/connection_respons.json | jq .
            fi
        else
            # If credentials are missing, wait and try again
            echo "CONNECTION - System is not ready to generate connection links (missing credentials from Agent)"
            sleep 4
            continue
        fi

        # Check if the response contains an error (e.g., still waiting for backend readiness)
        if echo "$CONNECTION_RESPONSE" | grep -q "error"; then
            echo "CONNECTION - Waiting for connection to Agent"
            sleep 1
        else
            break
        fi
    done

    # Extract client_id and token from the JSON response
    CLIENT_ID=$(get_data_attr "$CONNECTION_RESPONSE" "client_id")
    TOKEN=$(get_data_attr "$CONNECTION_RESPONSE" "token")

    # Check if OAKAGENT_APP_IDENTIFIER is set to 'com.luxonis.default', fully supported is only viewer. We need to rework this part to fully support static UI.
    if [[ "$OAKAGENT_APP_IDENTIFIER" == "com.luxonis.default" ]]; then
        export OAKAGENT_APP_IDENTIFIER="viewer"
    else
        export OAKAGENT_APP_IDENTIFIER="visualizer"
        export OAKAGENT_APP_VERSION="0.10.1"
    fi

    # Print instructions for accessing the DepthAI Viewer remotely and locally
    echo "CONNECTION - To connect DepthAI Viewer remotely, open:"
    echo "CONNECTION - https://public.luxonis.app/$OAKAGENT_APP_IDENTIFIER/$OAKAGENT_APP_VERSION/?t=$TOKEN&cid=$CLIENT_ID"
    echo "CONNECTION - (valid for 15 minutes)"
    echo "CONNECTION - To connect DepthAI Viewer locally, open: https://$IP:$OAKAPP_STATIC_FRONTEND_PORT"
}

# Loop that periodically refreshes the viewer connection link every ~10 minutes
connection_loop() {
    while true; do
        write_connection
        sleep 598  # 598 seconds = just under 10 minutes
    done
}

# Wait until the system time is valid (e.g., synced by NTP)
setup_loop() {
    while [[ "$(date +%Y)" == "1970" ]]; do
        echo "CONNECTION - System time is: $(date), which is invalid. Waiting for system time to be updated"
        sleep 3
    done
    echo "CONNECTION - System time is: $(date), starting the application"
}

# Run initial system time validation, then start the connection refresh loop
setup_loop
connection_loop