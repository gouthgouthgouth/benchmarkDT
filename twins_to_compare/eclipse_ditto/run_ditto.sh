#!/bin/bash

# Define variables
BRIDGE_NAME="br-ext"
MOSQUITTO_DOCKER_COMPOSE_LOCATION="/home/gauthier-le-tat/PycharmProjects/benchmarkDT/mosquitto"
DIND_DOCKER_COMPOSE_LOCATION="/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/eclipse_ditto"
NETWORK_NAME="external_network"
MOSQUITTO_CONTAINER="mosquitto"
DIND_CONTAINER="docker-host"

# Check if the Docker network exists
if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
    echo "Network $NETWORK_NAME does not exist. Creating it now..."
    docker network create --driver=bridge $NETWORK_NAME
    echo "Network $NETWORK_NAME created and attached to bridge $BRIDGE_NAME."
else
    echo "Network $NETWORK_NAME already exists."
fi

# Start containers
cd "$MOSQUITTO_DOCKER_COMPOSE_LOCATION" || exit
docker compose up -d &
gnome-terminal -- bash -c "cd $DIND_DOCKER_COMPOSE_LOCATION && docker compose up"

# Wait for both containers to be up
echo "Waiting for $MOSQUITTO_CONTAINER and $DIND_CONTAINER to start..."
while ! (docker ps --format '{{.Names}}' | grep -q "^$MOSQUITTO_CONTAINER$" && docker ps --format '{{.Names}}' | grep -q "^$DIND_CONTAINER$"); do
    sleep 5
    echo "Waiting for $MOSQUITTO_CONTAINER and $DIND_CONTAINER to start..."
done
echo "Both containers are running."

# Connect containers to the network only if they are not already connected
if ! docker network inspect external_network | grep -q "$MOSQUITTO_CONTAINER"; then
    docker network connect external_network "$MOSQUITTO_CONTAINER"
fi
if ! docker network inspect external_network | grep -q "$DIND_CONTAINER"; then
    docker network connect external_network "$DIND_CONTAINER"
fi

echo "Attaching to mosquitto for logs."

docker logs -f mosquitto