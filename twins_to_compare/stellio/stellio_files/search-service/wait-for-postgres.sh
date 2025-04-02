#!/bin/sh
echo "⏳ Waiting for postgres at $DB_HOST:$DB_PORT..."

until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

echo "✅ Postgres is up - starting application"
exec java -Xms256m -Xmx768m -jar application.jar