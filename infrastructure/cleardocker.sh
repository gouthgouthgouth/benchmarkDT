#!/bin/bash
# 1. Stopper tous les conteneurs
docker stop $(docker ps -aq)

# 2. Supprimer tous les conteneurs
docker rm -f $(docker ps -aq)

# 3. Supprimer tous les volumes
docker volume rm $(docker volume ls -q)

docker system prune -a --volumes -f

sleep 10