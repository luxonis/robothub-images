#!/bin/bash
echo "NGINX - Starting"

# Determine frontend configuration: either serve static files or proxy to backend
if [ -z "$OAKAPP_STATIC_FRONTEND_PATH" ]; then
    # No static path defined: fallback to reverse proxy
    export OAKAPP_STATIC_FRONTEND_CONFIGURATION='proxy_pass http://127.0.0.1:8082;'
else
    # Static path defined: serve frontend files directly
    export OAKAPP_STATIC_FRONTEND_CONFIGURATION="root $OAKAPP_STATIC_FRONTEND_PATH; index index.html; try_files \$uri \$uri/ /index.html;"
fi

# Replace placeholders in the NGINX config with env variables (limited to specific ones)
envsubst '${OAKAPP_STATIC_FRONTEND_CONFIGURATION} ${OAKAPP_STATIC_FRONTEND_PORT} ${OAKAPP_STATIC_FRONTEND_PATH}' \
    < /etc/nginx/sites-available/default \
    > /tmp/default.tmp

# Apply the updated configuration
mv /tmp/default.tmp /etc/nginx/sites-available/default

# NGINX related configuration files and folders

# Output the final configuration for debugging purposes
# echo "NGINX - Server configuration:"
# cat /etc/nginx/sites-available/default
# echo "NGINX - Global configuration:"
# cat /etc/nginx/nginx.conf

# Output Files in frontenf folder
# echo "Listing contents of $OAKAPP_STATIC_FRONTEND_PATH"
# if [ -d "$OAKAPP_STATIC_FRONTEND_PATH" ]; then
#    ls -al "$OAKAPP_STATIC_FRONTEND_PATH"
# else
#    echo "Directory $OAKAPP_STATIC_FRONTEND_PATH does not exist."
# fi

# Start NGINX in the foreground (needed for Docker containers or supervision)
exec nginx -g "daemon off;"