#!/bin/bash

# This script sets up Nginx with a self-signed SSL certificate and a basic configuration.
mkdir -p /etc/nginx/ssl

# Create SSL certificate and key
echo "NGINX - Generating self-signed SSL certificate"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx-selfsigned.key \
  -out /etc/nginx/ssl/nginx-selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=Department/CN=localhost"

echo "NGINX - SSL Configuration completed."