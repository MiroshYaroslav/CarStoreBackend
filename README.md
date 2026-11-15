# BMW Catalog API

FastAPI service for the BMW vehicle catalog. It provides product and category data, customer accounts, authentication, carts, favorites, reviews, orders, and synchronous/asynchronous callback requests. Product images are uploaded to Amazon S3 and served via CloudFront, while Redis and AWS SQS power read caching, request idempotency, and background task processing.

## Deployed application

- Frontend website: [https://auto-catalog.app/](https://auto-catalog.app/)
- Backend API: [https://api.auto-catalog.app/](https://api.auto-catalog.app/)
- API documentation (Swagger UI): [https://api.auto-catalog.app/docs](https://api.auto-catalog.app/docs)
- OpenAPI schema: [https://api.auto-catalog.app/api/v1/openapi.json](https://api.auto-catalog.app/api/v1/openapi.json)
- Legacy AWS load balancer URL: [http://bmw-cat-dev-1292959207.eu-central-1.elb.amazonaws.com](http://bmw-cat-dev-1292959207.eu-central-1.elb.amazonaws.com) (redirects to the HTTPS API address above)

The ACM certificate attached to the load balancer covers `api.auto-catalog.app`, and the DNS record points to the Terraform-provisioned Application Load Balancer.

## Architecture & Performance Reports

Detailed implementation notes, load testing results, cost calculations, and production verification screenshots are available in `docs/`:

- [Load Testing Scenario & Results](docs/LOADTEST.md)
- [Read Caching with Redis (Cache-Aside)](docs/CACHE.md)
- [ECS Target Tracking Auto Scaling](docs/AUTOSCALING.md)
- [CloudWatch Alerts & SNS Notifications](docs/ALERTS.md)
- [Asynchronous Task Queue (AWS SQS + ECS Worker)](docs/QUEUE.md)
- [API Idempotency (`Idempotency-Key` + Redis)](docs/IDEMPOTENCY.md)
- [Scheduled Auto Scaling & Cost Optimization](docs/SCHEDULE.md)

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis (for read caching and `Idempotency-Key` deduplication)
- AWS S3, CloudFront, and SQS credentials/resources (for image uploads and async task processing)

The API uses PostgreSQL through `asyncpg`. It does not create tables at startup; Alembic manages the database schema.

## Local setup

Install the locked dependencies and create a local environment file:

```powershell
uv sync
Copy-Item .env.example .env
```

Edit `.env` and configure:

- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` for a reachable PostgreSQL instance.
- `REDIS_URL` and `CACHE_ENABLED` for Redis caching and idempotency checks.
- `CORS_ORIGINS` as a JSON array containing allowed frontend origins, for example `["https://auto-catalog.app"]`.
- `SECRET_KEY` replaced with a randomly generated value:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Leave `AWS_BUCKET_NAME`, `AWS_CLOUDFRONT_DOMAIN`, and `SQS_QUEUE_URL` empty if you are not testing S3 uploads or SQS queues locally. On AWS ECS, credentials are supplied automatically via IAM task roles—never commit AWS keys or `.env` files.

## Database

For a new, empty database, apply all Alembic migrations:

```powershell
uv run alembic upgrade head
```

If the database already has tables from an earlier version, back it up and compare its schema with the current models before stamping:

```powershell
uv run alembic stamp head
```

Do not run `upgrade head` on an existing, unversioned database until you have confirmed that the initial migration will not recreate existing tables.

## Run the API & Worker

Start the FastAPI server:

```powershell
uv run uvicorn app.main:app --reload
```

Start the background SQS consumer worker (in a separate terminal when `SQS_QUEUE_URL` is configured):

```powershell
uv run python -m app.worker
```

The API listens on `http://127.0.0.1:8000`. Interactive documentation is at `/docs`; the OpenAPI schema is at `/api/v1/openapi.json`.

Most endpoints are under `/api/v1`:

- `auth` and `users`
- `products` and `categories`
- `cart` and `favorites`
- `orders` and `reviews`
- `callback-requests` (including `POST /api/v1/callback-requests/async` with `Idempotency-Key` header and `GET /api/v1/callback-requests/tasks/{task_id}`)

The login endpoint accepts OAuth2 form fields (`username` and `password`) at `POST /api/v1/auth/token`.

## Product images

Upload an image with `POST /api/v1/products/{product_id}/image` as multipart form data using the `file` field and a Bearer access token. In AWS, the Terraform-created S3 bucket remains private; CloudFront serves images through Origin Access Control, while the ECS task role can write only under `products/`.

Set `product_image_upload_allowed_user_ids` in the untracked `terraform/terraform.tfvars` to the UUIDs of catalog administrators (`GET /api/v1/auth/me`). The API accepts JPEG, PNG, and WebP files up to 5 MiB and saves the CloudFront URL in the selected product's `image_url` field.

Users can create, update, or delete only their own reviews. Favorites and order history are scoped to the authenticated user. Cart operations use either the authenticated user's cart or a guest `session_id`; guest clients must send that same `session_id` when deleting an item (`DELETE /api/v1/cart/{item_id}?session_id=...`).

## Tests, load testing & formatting

Run the test suite (including idempotency and API contract tests):

```powershell
uv run python -m pytest
```

Run the Locust load test against the deployed or local API:

```powershell
LOADTEST_MAX_USERS=200 uv run locust -f loadtest/locustfile.py --host=[https://api.auto-catalog.app](https://api.auto-catalog.app) --csv=results/loadtest --html=results/loadtest.html
```

Format Python files and sort imports with Ruff:

```powershell
uv run ruff format app migrations tests
uv run ruff check --fix app migrations tests
```

To check formatting without modifying files:

```powershell
uv run ruff format --check app migrations tests
uv run ruff check app migrations tests
```

## Docker

Start the API and PostgreSQL locally from the project root:

```powershell
Copy-Item .env.example .env  # only needed the first time
docker compose up --build
```

Compose waits for PostgreSQL to become healthy, applies Alembic migrations, and starts the API on `http://127.0.0.1:8000/docs`. Stop the stack with `docker compose down`, or remove volumes with `docker compose down --volumes`.

The production image runs as a non-root user and contains the API, worker module, and migrations. In ECS, configuration is injected via task definitions and AWS Secrets Manager.

## AWS deployment

Pushing to `main` triggers the GitHub Actions workflow (`.github/workflows/deploy.yml`), which builds a Docker image tagged with the commit SHA, pushes it to Amazon ECR, runs `alembic upgrade head` as a one-off Fargate task, and updates both ECS services (`bmw-catalog-dev-service` and `bmw-catalog-dev-worker-service`) only after the migration succeeds.

Infrastructure in `terraform/` provisions:

- VPC, private/public subnets, NAT Gateway, Security Groups, and Application Load Balancer
- Amazon RDS (PostgreSQL) and AWS Secrets Manager
- Amazon ECS Fargate cluster running the API + Redis sidecar container and the SQS background worker service
- Amazon SQS task queue (`bmw-catalog-dev-task-queue`) with queue-depth Target Tracking scaling for the worker
- CPU Target Tracking Auto Scaling, day/night Scheduled Auto Scaling (`cron(0 8 * * ? *)` and `cron(0 20 * * ? *)`), and CloudWatch CPU alarms with SNS email notifications
- Private S3 bucket and CloudFront distribution with OAC

## Project layout

```text
app/
  api/                 FastAPI dependencies and versioned routes
    v1/endpoints/      Request handlers (catalog, auth, cart, orders, async callbacks)
  core/                Settings, database engine, Redis client, idempotency, and JWT helpers
  exceptions/          Application exceptions and HTTP handlers
  middlewares/         Request timing middleware
  models/              SQLAlchemy models (including AsyncTask)
  repositories/        Database queries
  schemas/             Pydantic request and response models
  services/            Business logic, S3 uploads, and SQS task publishing
  main.py              FastAPI application entrypoint
  worker.py            Background AWS SQS consumer service
docs/                  Performance, caching, scaling, queue, and architecture reports
loadtest/              Locust load testing scripts
migrations/            Alembic configuration and revisions
results/               Saved Locust CSV and HTML reports
terraform/             AWS infrastructure as code (VPC, RDS, ECS, SQS, S3, CloudWatch)
tests/                 API contract, auth, and idempotency tests
pyproject.toml         Runtime and development dependencies
uv.lock                Resolved dependency versions
Dockerfile             Production container image
compose.yaml           Local API and PostgreSQL stack
.github/workflows/     GitHub Actions CI/CD deployment workflow
```

When changing a SQLAlchemy model, generate and review a migration before applying it:

```powershell
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```