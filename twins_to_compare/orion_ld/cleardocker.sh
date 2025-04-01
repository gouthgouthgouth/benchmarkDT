#!/bin/bash
docker stop mosquitto orion_ld-orion-ld-1 orion_ld-mongo-orion-1 orion_ld-mongo-iot-1 orion_ld-iot-agent-1
docker system prune -a --volumes -f

echo "All cleaned."