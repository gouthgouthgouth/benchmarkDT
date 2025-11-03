#!/bin/bash

# Define variables
MOSQUITTO_DOCKER_COMPOSE_LOCATION="/home/gauthier-le-tat/PycharmProjects/benchmarkDT/mosquitto"
NETWORK_NAME="external_network"
DITTO_DOCKER_COMPOSE_LOCATION="/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/eclipse_ditto/ditto/deployment/docker"
CONTAINERS=("docker-gateway-1" "docker-nginx-1" "docker-things-1" "docker-things-search-1" "docker-connectivity-1" "docker-policies-1" "mosquitto")

# Check if the Docker network exists
if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
    echo "Network $NETWORK_NAME does not exist. Creating it now..."
    docker network create --driver=bridge $NETWORK_NAME
    echo "Network $NETWORK_NAME created."
else
    echo "Network $NETWORK_NAME already exists."
fi

# Start containers
cd $MOSQUITTO_DOCKER_COMPOSE_LOCATION
docker compose up -d &
cd $DITTO_DOCKER_COMPOSE_LOCATION
docker compose up -d &

# Wait for all containers to be healthy
echo "Waiting for containers to be healthy..."
while true; do
    ALL_HEALTHY=true
    for C in "${CONTAINERS[@]}"; do
        STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$C" 2>/dev/null)
        if [[ "$STATUS" != "healthy" ]]; then
            ALL_HEALTHY=false
            echo "Waiting for $C to become healthy..."
        fi
    done
    $ALL_HEALTHY && break
    sleep 5
done
echo "All containers are healthy."

# Connect containers to the network only if they are not already connected
for C in "${CONTAINERS[@]}"; do
    if ! docker network inspect external_network | grep -q "$C"; then
        docker network connect external_network "$C"
        echo "Connected $C to external_network"
    fi
done

echo "All containers are running."