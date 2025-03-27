#!/bin/bash
docker stop mosquitto fiware-scorpio-1 fiware-postgres-1 fiware-iot-agent-1 db-mongo
docker system prune -a --volumes -f

echo "All cleaned."