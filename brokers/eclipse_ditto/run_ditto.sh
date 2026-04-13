#!/bin/bash

# Define variables
PROJECT_ROOT="$(pwd)"
MOSQUITTO_DOCKER_COMPOSE_LOCATION="$PROJECT_ROOT/infrastructure/mosquitto"
DITTO_DOCKER_COMPOSE_LOCATION="$PROJECT_ROOT/brokers/eclipse_ditto/ditto/deployment/docker"
NETWORK_NAME="external_network"
CONTAINERS=("docker-gateway-1" "docker-things-1" "docker-things-search-1" "docker-connectivity-1" "docker-policies-1" "mosquitto")
echo ok
# Check if the Docker network exists
if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
    echo "Network $NETWORK_NAME does not exist. Creating it now..."
    docker network create --driver=bridge $NETWORK_NAME
    echo "Network $NETWORK_NAME created."
else
    echo "Network $NETWORK_NAME already exists."
fi

# Start containers
cd "$DITTO_DOCKER_COMPOSE_LOCATION"
docker compose up -d &

# Start containers
cd "$MOSQUITTO_DOCKER_COMPOSE_LOCATION" || exit
docker compose up -d &

# Wait for all containers to be healthy
echo "Waiting for containers to be healthy..."

declare -A PREV_STATUS
for C in "${CONTAINERS[@]}"; do
  PREV_STATUS[$C]="not healthy"
done
while true; do
  ALL_HEALTHY=true
  for C in "${CONTAINERS[@]}"; do
      STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$C" 2>/dev/null)
      if [[ "$STATUS" != "healthy" ]]; then
          ALL_HEALTHY=false
          echo "Waiting for $C to become healthy..."
      fi
      if [[ "${PREV_STATUS[$C]}" != "healthy" && "$STATUS" == "healthy" ]]; then
          echo "Conteneur $C is now healthy"
      fi
      PREV_STATUS[$C]="$STATUS"
  done
  if [[ "$ALL_HEALTHY" == true ]]; then
    break
  fi
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