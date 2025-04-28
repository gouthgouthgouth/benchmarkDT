#!/bin/bash
docker stop mosquitto stellio-search stellio-kafka stellio-zookeeper stellio-postgres iot-agent db-mongo
docker system prune -a --volumes -f

echo "All cleaned."