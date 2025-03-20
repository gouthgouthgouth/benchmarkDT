#!/bin/bash

CONTAINER_NAME="docker-things-1"
OUTPUT_FILE=./measures/"$(date +"%Y-%m-%d_%H-%M-%S")-things"

if [ -z "$CONTAINER_NAME" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: $0 <container_name> <output_file>"
  exit 1
fi

echo "Redirecting logs from container '$CONTAINER_NAME' to file '$OUTPUT_FILE'..."
docker logs -f "$CONTAINER_NAME" &> "$OUTPUT_FILE"
