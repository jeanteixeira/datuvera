#!/bin/sh
set -eu

# This command targets only the fixed demo service/database. No volume is removed.
docker compose up -d --wait datuvera-demo-db
printf '%s\n' 'Resetting public schema in datuvera-demo-db/demo only.'
# Read the seed before starting the transaction; a missing file cannot reset the schema.
seed_sql=$(cat docker/postgres/demo/init/01_create_demo.sql)
{
    printf '%s\n' 'DROP SCHEMA public CASCADE;' 'CREATE SCHEMA public AUTHORIZATION demo;'
    printf '%s\n' "$seed_sql"
} | docker compose exec -T datuvera-demo-db psql -U demo -d demo --single-transaction -v ON_ERROR_STOP=1
printf '%s\n' 'Demo reset complete. Internal database and volumes were not touched.'
