#!/bin/bash
docker stop docker-connectivity-1 docker-gateway-1 docker-policies-1 docker-things-search-1 docker-ditto-ui-1 docker-mongodb-1 docker-things-1 mosquitto docker-nginx-1 docker-swagger-ui-1
docker system prune -a --volumes -f

echo "All cleaned."