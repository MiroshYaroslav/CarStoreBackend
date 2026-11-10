# Load test

The Locust profile is read-heavy: ten GET task types and one persistent write
task, with equal task weights. It ramps from zero to the configured user count
in 2.5 minutes, holds for five minutes, and ramps down over two minutes. Each
virtual user waits 0.5–1.5 seconds between tasks.

The application does not expose `POST /api/v1/products/`. The write task uses
`POST /api/v1/callback-requests/`, the public persistent create endpoint. It
creates database rows, so run only against a disposable test/staging database.
Product/category data are discovered at startup; seed at least one product for
detail requests and one category for category filtering.

Install Locust in an isolated environment, then run from the repository root:

```powershell
uv run --with locust locust -f loadtest/locustfile.py --host https://api.example.com --headless --csv docs/results/loadtest --html docs/results/loadtest.html
```

Set `LOADTEST_MAX_USERS` (default 40) and `LOADTEST_SPAWN_RATE` (default 4
users/second) in the environment before launch. The host must be the API origin;
the script includes `/api/v1` paths. The full run lasts about 9.5 minutes.
Locust reports request rate, failures, and latency percentiles (including
median/p50, p95, and p99). Save its CSV/HTML output and record the observed
values below; do not substitute estimates.

## Results

| Run date / environment | Peak users | RPS | p50 | p95 | p99 | Error rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pending execution | — | — | — | — | — | — |

The per-request Locust statistics distinguish product listing, details, and
the write endpoint. Include both overall and endpoint-level results in the
submission after the test runs.
