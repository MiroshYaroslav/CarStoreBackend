# BMW Catalog API

FastAPI service for the BMW vehicle catalog. It provides product and category data, customer accounts, authentication, carts, favorites, reviews, orders, and callback requests. Product images are uploaded to Amazon S3; the API stores the resulting URL with the product.

## Deployed application

- Application: http://bmw-cat-dev-1292959207.eu-central-1.elb.amazonaws.com
- API documentation (Swagger UI): http://bmw-cat-dev-1292959207.eu-central-1.elb.amazonaws.com/docs
- OpenAPI schema: http://bmw-cat-dev-1292959207.eu-central-1.elb.amazonaws.com/api/v1/openapi.json

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- AWS bucket and credentials for image uploads

The API uses PostgreSQL through `asyncpg`. It does not create tables at startup; Alembic manages the schema.

## Local setup

Install the locked dependencies and create a local environment file:

```powershell
uv sync
Copy-Item .env.example .env
```

Edit `.env` and set `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` for a reachable PostgreSQL database. Set `CORS_ORIGINS` to a JSON array containing the frontend origin or origins, for example `["https://catalog.example.com"]`. Replace the example `SECRET_KEY` with a randomly generated value. For example:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The example includes every setting the application expects. Leave `AWS_BUCKET_NAME` empty if you are not using image uploads locally; set it and `AWS_REGION` when you configure S3. The AWS SDK uses its standard credential chain, so for local development you can use an AWS profile; on ECS, assign S3 permissions to the task role. Do not put AWS access keys in `.env` or commit them.

## Database

For a new, empty database, apply the migrations:

```powershell
uv run alembic upgrade head
```

If the database already has tables from an earlier version, back it up and compare its schema with the current models before using `stamp`. Stamping records the migration version without changing the tables:

```powershell
uv run alembic stamp head
```

Do not run `upgrade head` on an existing, unversioned database until you have confirmed that the initial migration will not recreate existing tables.

## Run the API

```powershell
uv run uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. Interactive documentation is at `/docs`; the OpenAPI schema is at `/api/v1/openapi.json`.

Most endpoints are under `/api/v1`. The main groups are:

- `auth` and `users`
- `products` and `categories`
- `cart` and `favorites`
- `orders` and `reviews`
- `callback-requests`

The login endpoint accepts OAuth2 form fields (`username` and `password`) at `POST /api/v1/auth/token`.

## Product images

Upload an image with `POST /api/v1/products/{product_id}/image` as multipart form data using the `file` field. The API uploads it to the configured bucket and saves its absolute S3 URL to the product record. Configure bucket access or a CDN so clients can read the returned URLs.

## Tests and formatting

Run the tests with:

```powershell
uv run pytest
```

Format Python files and sort imports with Ruff:

```powershell
uv run ruff format app migrations tests
uv run ruff check --fix app migrations tests
```

To check formatting without changing files:

```powershell
uv run ruff format --check app migrations tests
uv run ruff check app migrations tests
```

## Docker

Build and run the API image from the project root:

```powershell
docker build -t bmw-catalog-api .
docker run --rm -p 8000:8000 --env-file .env bmw-catalog-api
```

The image runs as a non-root user and contains the API and migrations, not the test suite or local environment file. Pass configuration at runtime. In ECS, set the required application variables in the task definition and use a task role for AWS access.

## AWS deployment

Pushing to `main` builds an image tagged with the commit SHA, runs `alembic upgrade head` as a one-off ECS task, and updates the ECS service only after the migration task exits successfully. Keep migrations backward-compatible with the currently running application version; use an expand-and-contract sequence for changes that remove or rename existing columns.

The callback contact directory is read-only through the API. Its initial entries are inserted by the Alembic migration; maintain the directory through a reviewed database migration rather than a public write endpoint.

## Project layout

```text
app/
  api/                 FastAPI dependencies and versioned routes
    v1/endpoints/      Request handlers
  core/                Settings, database engine, and JWT helpers
  exceptions/          Application exceptions and HTTP handlers
  middlewares/         Request timing middleware
  models/              SQLAlchemy models
  repositories/        Database queries
  schemas/             Pydantic request and response models
  services/            Application logic, including S3 uploads
migrations/            Alembic configuration and revisions
tests/                 API contract tests
pyproject.toml         Runtime and development dependencies
uv.lock                Resolved dependency versions
Dockerfile             Production container image
```

When changing a model, create and review a migration before applying it:

```powershell
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```
