#!/bin/bash

CONTAINER_NAME="mosquitto"
OUTPUT_FILE=./measures/"$(date +"%Y-%m-%d_%H-%M-%S")-mosquitto"

if [ -z "$CONTAINER_NAME" ]; then
  echo "Usage: $0 <container_name>"
  exit 1
fi

echo "Redirecting logs from container '$CONTAINER_NAME' to file '$OUTPUT_FILE' with timestamps..."

docker logs -f "$CONTAINER_NAME" | while IFS= read -r line
do
  echo "$(date +"%Y-%m-%d %H:%M:%S.%3N") $line" >> "$OUTPUT_FILE"
done
