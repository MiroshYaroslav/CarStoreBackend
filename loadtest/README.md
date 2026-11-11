# Load test

The Locust user journey creates one callback request, then performs nine product read operations. The API does not expose a public GET for callback requests, so reads cannot include the just-created record without adding an authenticated admin flow. Each user waits 0.5–1.5 seconds between requests.

The default shape is a 150-second ramp to 40 users, a 330-second plateau, and a 120-second ramp down (10 minutes total). For the full command and result-recording instructions, see [docs/LOADTEST.md](../docs/LOADTEST.md).

Example:

```powershell
$env:LOADTEST_MAX_USERS = "40"
$env:LOADTEST_SPAWN_RATE = "4"
uv run --with locust locust -f .\loadtest\locustfile.py --host https://api.auto-catalog.app --headless --csv .\docs\results\loadtest --csv-full-history --html .\docs\results\loadtest.html
```

The write operation persists data. Use a test environment and clean generated rows after each run.
