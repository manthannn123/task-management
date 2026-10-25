# Task Management System

A small three-tier application for learning Docker, AWS networking, and CI/CD.

## Architecture
- **Web:** Nginx serves the HTML/CSS/JavaScript frontend and proxies `/api/` to Flask.
- **App:** Python Flask REST API.
- **Database:** MySQL with a named Docker volume.

## Run locally
1. Copy `.env.example` to `.env`.
2. Change the development passwords in `.env`.
3. Run `docker compose up --build -d`.
4. Open http://localhost:8080.
5. View logs with `docker compose logs -f`.
6. Stop containers with `docker compose down`.

The database volume remains after `docker compose down`. To delete it too, run `docker compose down -v` (this permanently removes the volume data).

## Useful commands
```bash
docker compose ps
docker compose logs -f web
docker compose logs -f api
docker compose logs -f db
docker compose exec api sh
docker compose exec db mysql -u taskapp -p task_manager
```

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API and database connectivity |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/<id>` | Get one task |
| PUT | `/api/tasks/<id>` | Update a task |
| DELETE | `/api/tasks/<id>` | Delete a task |

Example:
```bash
curl -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Learn Docker volumes","description":"Test persistence","status":"pending"}'
```

## Project layout
```text
task-management-project/
├── frontend/       # Nginx, HTML, CSS, JavaScript
├── backend/        # Flask API, Dockerfile, tests
├── database/       # MySQL initialization SQL
├── .env.example
└── docker-compose.yml
```

## Security notes
- `.env.example` contains local-development defaults only. Change them and never commit your real `.env`.
- Do not expose MySQL publicly. In AWS, permit TCP 3306 only from the App tier and API traffic only from the Web tier.
- This is a learning project, not production-hardened. Production requires secret management, TLS, restricted ingress, backups, and a controlled database migration process.
- A named volume persists data across container replacement, but it is not a backup.
