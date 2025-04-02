#!/bin/bash
docker stop mosquitto stellio-search stellio-kafka stellio-zookeeper stellio-postgres
docker system prune -a --volumes -f

echo "All cleaned."