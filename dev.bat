docker compose -f compose.dev.yml down
docker volume rm progkeeper-controller_pk_data
docker volume rm progkeeper-controller_pk_db
docker compose -f compose.dev.yml up -d --build