#!/bin/bash

CONTAINER_NAME="scorpio-iot-agent-1"
OUTPUT_FILE=./twins_to_compare/scripts_for_measures/scorpio/measures/"$1-entities"

if [ -z "$CONTAINER_NAME" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: $0 <container_name> <output_file>"
  exit 1
fi

echo "Redirecting logs from container '$CONTAINER_NAME' to file '$OUTPUT_FILE'..."
docker logs -f --since 0s "$CONTAINER_NAME" &> "$OUTPUT_FILE" &
LOG_PID=$!

# Fonction de nettoyage à l'arrêt du script
cleanup() {
  echo "Stopping docker logs process with PID $LOG_PID"
  kill $LOG_PID 2>/dev/null
  wait $LOG_PID 2>/dev/null
  echo "Cleanup done."
}

# Définir le trap pour interruption (Ctrl+C) ou fin normale
trap cleanup EXIT

# Garder le script vivant jusqu'à interruption
wait $LOG_PID