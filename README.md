# Flask + ibm_db demo

This repository contains a minimal Flask app that can run queries against an IBM Db2 instance using the `ibm_db` package. It includes a Dockerfile for the Flask app and a docker-compose setup that can start a local Db2 container for development.

## Quickstart

1. Copy `.env.example` to `.env` (default values work with the included Db2 container)
2. Build and run with Docker Compose:

   ```powershell
   docker-compose up --build
   ```

   This will start:

   - Flask app on port 5000
   - Db2 container on port 50000 (exposed as 50000 in compose)

3. Wait for Db2 to initialize (can take a few minutes on first run)

4. Test the API:

   Health check:

   ```powershell
   curl http://localhost:5000/ping
   ```

   Query the test table:

   ```powershell
   curl -X POST http://localhost:5000/query `
        -H "Content-Type: application/json" `
        -d '{"sql": "SELECT * FROM USERS"}'
   ```

## Database initialization

The repo includes `init/01-init.sql`. The compose file mounts the `./init` directory into the Db2 container at `/docker-entrypoint-initdb.d` so the SQL file is available to the container. There are two ways to ensure the SQL is applied:

### A) Automatic initialization (recommended for first run)

If the Db2 data volume is empty, the container's entrypoint will execute scripts in `/docker-entrypoint-initdb.d` during first initialization.

Steps:

1. If you've started the stack before and want a fresh initialization, remove the existing volume first (this deletes existing DB data):

   ```powershell
   docker-compose down
   # list volumes to confirm the name if different
   docker volume ls
   docker volume rm ibm-db-docker-demo_db2data
   ```

2. Start the stack and watch logs:

   ```powershell
   docker-compose up --build
   docker-compose logs -f db2
   ```

   The init script will run during first-boot. Wait until logs show the DB is ready and healthcheck passes.

### B) Manual execution (re-run or apply to an existing DB)

If the database already exists or you need to re-run the script, exec into the running Db2 container and run the file with the `db2` CLI.

1. Start containers if not running:

   ```powershell
   docker-compose up -d
   ```

2. Get the container name (example name may vary):

   ```powershell
   docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
   ```

3. Exec into the container and run the SQL as the Db2 instance user:

   ```powershell
   docker exec -it <db2-container-name> bash
   # inside the container (bash prompt)
   su - db2inst1
   . /database/config/db2inst1/sqllib/db2profile
   db2 connect to users user db2inst1 using password
   db2 -tvf /docker-entrypoint-initdb.d/01-init.sql
   db2 connect reset
   exit
   exit
   ```

Replace `<db2-container-name>` with the container name shown by `docker ps` and change `users`, `db2inst1`, and `password` where appropriate if you modified `.env`.

### Verify

Use the Flask API to query the `USERS` table:

```powershell
curl -X POST http://localhost:5000/query -H "Content-Type: application/json" -d '{"sql":"SELECT * FROM USERS"}'
```

Or run a db2 query inside the container (see manual exec above).

## Notes

- Db2 first-time initialization can take several minutes; check logs with `docker-compose logs -f db2`.
- If init didn't run automatically, it's usually because the DB volume already existed; remove the volume to force first-boot behavior.
- For production, do not store credentials in `.env`; use a secrets manager and stronger passwords.

## Using `.env` and keeping secrets out of git

This project ships `.env.example`. Copy it to `.env` and update values for your environment. The compose file is configured to load environment variables from `.env` for both the `web` and `db2` services.

```powershell
copy .env.example .env
# edit .env with your real values
notepad .env
docker-compose up --build
```

`.env` is ignored by `.gitignore` that was added to this repo, so your local secrets won't be committed.
