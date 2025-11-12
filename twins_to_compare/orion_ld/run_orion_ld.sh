#!/bin/bash

# Define variables
PROJECT_ROOT="$(pwd)"
MOSQUITTO_DOCKER_COMPOSE_LOCATION="$PROJECT_ROOT/mosquitto"
FIWARE_DOCKER_COMPOSE_LOCATION="$PROJECT_ROOT/twins_to_compare/orion_ld"

MOSQUITTO_CONTAINER="mosquitto"
ORION_CONTAINER="orion_ld-orion-ld-1"
MONGO_ORION_CONTAINER="orion_ld-mongo-orion-1"
IOT_AGENT_CONTAINER="orion_ld-iot-agent-1"
MONGO_IOT_CONTAINER="orion_ld-mongo-iot-1"
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
cd $FIWARE_DOCKER_COMPOSE_LOCATION
docker compose up -d

# Wait for containers to be up
echo "Waiting for $MOSQUITTO_CONTAINER and Fiware containers to start..."
while ! (docker ps --format '{{.Names}}' | grep -q "^$MOSQUITTO_CONTAINER$" && \
         docker ps --format '{{.Names}}' | grep -q "^$ORION_CONTAINER$" && \
         docker ps --format '{{.Names}}' | grep -q "^$MONGO_ORION_CONTAINER$" && \
         docker ps --format '{{.Names}}' | grep -q "^$IOT_AGENT_CONTAINER$" && \
         docker ps --format '{{.Names}}' | grep -q "^$MONGO_IOT_CONTAINER$"); do
    sleep 5
    echo "Waiting for containers to start..."
done
echo "All containers are running."

# Connect containers to the network if they are not already connected
for container in $MOSQUITTO_CONTAINER $ORION_CONTAINER $MONGO_ORION_CONTAINER $IOT_AGENT_CONTAINER $MONGO_IOT_CONTAINER; do
    if ! docker network inspect $NETWORK_NAME | grep -q "$container"; then
        docker network connect $NETWORK_NAME "$container"
    fi
done