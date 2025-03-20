cd root/ditto/deployment/docker/
docker compose up -d

CONTAINER_NAME="docker-nginx-1"

docker cp $(pwd)/nginx.conf $CONTAINER_NAME:/etc/nginx/nginx.conf
docker cp $(pwd)/nginx.htpasswd $CONTAINER_NAME:/etc/nginx/nginx.htpasswd
docker cp $(pwd)/nginx-cors.conf $CONTAINER_NAME:/etc/nginx/nginx-cors.conf
docker cp $(pwd)/mime.types $CONTAINER_NAME:/etc/nginx/mime.types
docker cp $(pwd)/index.html $CONTAINER_NAME:/usr/share/nginx/html/index.html
docker cp $(pwd)/../../documentation/src/main/resources/images $CONTAINER_NAME:/usr/share/nginx/html/images
docker cp $(pwd)/../../documentation/src/main/resources/wot $CONTAINER_NAME:/usr/share/nginx/html/wot

CONTAINER_NAME="docker-swagger-ui-1"

docker cp $(pwd)/../../documentation/src/main/resources/openapi $CONTAINER_NAME:/usr/share/nginx/html/openapi
docker cp $(pwd)/../../documentation/src/main/resources/images $CONTAINER_NAME:/usr/share/nginx/html/images
docker cp $(pwd)/swagger3-index.html $CONTAINER_NAME:/usr/share/nginx/html/index.html

sleep infinity