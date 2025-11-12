#!/bin/bash

# Define variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOSQUITTO_DOCKER_COMPOSE_LOCATION="$SCRIPT_DIR/mosquitto"
FIWARE_DOCKER_COMPOSE_LOCATION="$SCRIPT_DIR/twins_to_compare/stellio/stellio_files"
MOSQUITTO_CONTAINER="mosquitto"
STELLIO_SEARCH_CONTAINER="stellio-search"
POSTGRES_CONTAINER="stellio-postgres"
KAFKA_CONTAINER="stellio-kafka"
ZOOKEEPER_CONTAINER="stellio-zookeeper"
IOT_AGENT_CONTAINER="iot-agent"
MONGODB_CONTAINER="db-mongo"
NETWORK_NAME="external_network"

# Check if the Docker network exists
if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
    echo "Network $NETWORK_NAME does not exist. Creating it now..."
    docker network create --driver=bridge $NETWORK_NAME
    echo "Network $NETWORK_NAME created."
else
    echo "Network $NETWORK_NAME already exists."
fi

# Start containers
cd "$MOSQUITTO_DOCKER_COMPOSE_LOCATION" || exit
docker compose up -d &
gnome-terminal -- bash -c "cd $FIWARE_DOCKER_COMPOSE_LOCATION && docker compose up"

# Wait for containers to be up
echo "Waiting for containers to start..."
while ! (
    docker ps --format '{{.Names}}' | grep -q "^$MOSQUITTO_CONTAINER$" &&
    docker ps --format '{{.Names}}' | grep -q "^$STELLIO_SEARCH_CONTAINER$" &&
    docker ps --format '{{.Names}}' | grep -q "^$POSTGRES_CONTAINER$" &&
    docker ps --format '{{.Names}}' | grep -q "^$KAFKA_CONTAINER$" &&
    docker ps --format '{{.Names}}' | grep -q "^$ZOOKEEPER_CONTAINER$" &&
    docker ps --format '{{.Names}}' | grep -q "^$IOT_AGENT_CONTAINER$" &&
    docker ps --format '{{.Names}}' | grep -q "^$MONGODB_CONTAINER$"
); do
    sleep 5
    echo "Waiting for containers to be ready..."
done
echo "All containers are running."

# Connect containers to the network if not already connected
for container in "$MOSQUITTO_CONTAINER" "$STELLIO_SEARCH_CONTAINER" "$POSTGRES_CONTAINER" "$KAFKA_CONTAINER" "$ZOOKEEPER_CONTAINER" "$IOT_AGENT_CONTAINER" "$MONGODB_CONTAINER"; do
    if ! docker network inspect "$NETWORK_NAME" | grep -q "$container"; then
        docker network connect "$NETWORK_NAME" "$container"
    fi
done
