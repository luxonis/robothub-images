#!/bin/bash

# Function that waits until required system conditions are met before starting oak_webrtc
setup_loop() {
    while [[ -z "$OAKAGENT_PRIVATE_HTTP_PWD" || -z "$OAKAGENT_CONTAINER_ID" || "$(date +%Y)" == "1970" ]]; do
        # Conditions:
        # - Agent password is not yet available
        # - Container ID is not yet available
        # - System time is still at epoch start (e.g., no NTP sync yet)
        echo "OAK_WEBRTC - System is not ready to start oak_webrtc (missing credentials from Agent)"
        sleep 4
    done
    echo "OAK_WEBRTC - Starting"
}

# Call the setup loop to wait for system readiness
setup_loop

# Set the HTTP endpoint of the local agent used for registration
export OAKAGENT_PRIVATE_HTTP_ENDPOINT=127.0.0.1:9091

# Replace the shell process with the oak_webrtc binary (ensures proper signal handling in Docker)
exec oak_webrtc