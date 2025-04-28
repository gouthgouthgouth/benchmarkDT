#!/bin/bash
docker stop mosquitto scorpio-scorpio-1 scorpio-postgres-1 scorpio-iot-agent-1 db-mongo
docker system prune -a --volumes -f
docker volume rm $(docker volume ls -q)

echo "All cleaned."