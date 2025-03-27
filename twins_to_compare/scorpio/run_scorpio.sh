#!/bin/bash

# Define variables
MOSQUITTO_DOCKER_COMPOSE_LOCATION="/home/gauthier-le-tat/PycharmProjects/benchmarkDT/mosquitto"
FIWARE_DOCKER_COMPOSE_LOCATION="/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/scorpio"
MOSQUITTO_CONTAINER="mosquitto"
SCORPIO_CONTAINER="fiware-scorpio-1"
POSTGRES_CONTAINER="fiware-postgres-1"
IOT_AGENT_CONTAINER="fiware-iot-agent-1"
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

# Wait for both containers to be up
echo "Waiting for $MOSQUITTO_CONTAINER and Fiware containers to start..."
while ! (docker ps --format '{{.Names}}' | grep -q "^$MOSQUITTO_CONTAINER$" && docker ps --format '{{.Names}}' | grep -q "$IOT_AGENT_CONTAINER$" && docker ps --format '{{.Names}}' | grep -q "^$POSTGRES_CONTAINER$" && docker ps --format '{{.Names}}' | grep -q "^$SCORPIO_CONTAINER$" && docker ps --format '{{.Names}}' | grep -q "^$MONGODB_CONTAINER$"); do
    sleep 5
    echo "Waiting for $MOSQUITTO_CONTAINER and Fiware containers to start..."
done
echo "All containers are running."

# Connect containers to the network only if they are not already connected
if ! docker network inspect external_network | grep -q "$MOSQUITTO_CONTAINER"; then
    docker network connect external_network "$MOSQUITTO_CONTAINER"
fi
if ! docker network inspect external_network | grep -q "$SCORPIO_CONTAINER"; then
    docker network connect external_network "$SCORPIO_CONTAINER"
fi
if ! docker network inspect external_network | grep -q "$POSTGRES_CONTAINER"; then
    docker network connect external_network "$POSTGRES_CONTAINER"
fi
if ! docker network inspect external_network | grep -q "$IOT_AGENT_CONTAINER"; then
    docker network connect external_network "$IOT_AGENT_CONTAINER"
fi
if ! docker network inspect external_network | grep -q "$MONGODB_CONTAINER"; then
    docker network connect external_network "$MONGODB_CONTAINER"
fi