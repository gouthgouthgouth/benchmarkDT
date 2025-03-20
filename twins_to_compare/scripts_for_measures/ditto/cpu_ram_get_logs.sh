#!/bin/bash

CONTAINER_NAME="docker-host"
OUTPUT_FILE=./measures/"$(date +"%Y-%m-%d_%H-%M-%S")-cpu_ram"

echo "Starting CPU/RAM monitoring for container '$CONTAINER_NAME'..."
echo "Timestamp, CPU%, Mem%" > "$OUTPUT_FILE"

trap "echo 'Terminal closed, stopping monitoring.'; exit 0" SIGHUP SIGINT SIGTERM

while true; do
  STATS=$(docker stats $CONTAINER_NAME --no-stream --format "{{.CPUPerc}},{{.MemPerc}}")
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S.%3N")
  echo "$TIMESTAMP, $STATS" >> "$OUTPUT_FILE"
  sleep 0.1
done
