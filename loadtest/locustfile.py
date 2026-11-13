"""Read-heavy load profile for the deployed BMW Catalog API.

Configure LOCUST_HOST and LOADTEST_MAX_USERS before running. The write task
creates callback requests because this API intentionally has no product-create
endpoint. Use a test/staging environment: writes persist in PostgreSQL.
"""

import os
import random
import uuid

from locust import HttpUser, LoadTestShape, between, task


class CatalogUser(HttpUser):
    wait_time = between(0.5, 1.5)
    products: list[dict] = []
    categories: list[dict] = []

    def on_start(self):
        if not type(self).products:
            response = self.client.get("/api/v1/products/", name="GET products (seed)")
            if response.ok:
                type(self).products = response.json()
        if not type(self).categories:
            response = self.client.get("/api/v1/categories/", name="GET categories (seed)")
            if response.ok:
                type(self).categories = response.json()

    @task(1)
    def read_heavy_journey(self):
        """One persistent write followed by nine reads, repeated per user."""
        suffix = uuid.uuid4().hex[:10]
        response = self.client.post(
            "/api/v1/callback-requests/",
            json={
                "name": "Load test",
                "phone": f"+38099{random.randint(1000000, 9999999)}",
                "description": f"Automated load test {suffix}",
            },
            name="POST callback request (write)",
        )
        # Callback reads require admin authentication, so this catalog API's
        # public read operations are used for the read-heavy portion instead.
        products = type(self).products
        for index in range(9):
            self.wait()
            if index % 3 == 2 and products:
                product_id = random.choice(products)["id"]
                self.client.get(f"/api/v1/products/{product_id}", name="GET product detail")
            else:
                paths = (
                    "/api/v1/products/",
                    "/api/v1/products/?search=BMW",
                    "/api/v1/products/?sort=price-desc",
                )
                self.client.get(random.choice(paths), name="GET products read")


class CatalogLoadShape(LoadTestShape):
    """Ramp up for 2.5m, hold 5m, then ramp down for 2m."""

    ramp_seconds = 150
    hold_seconds = 330
    down_seconds = 120

    def tick(self):
        elapsed = self.get_run_time()
        max_users = int(os.getenv("LOADTEST_MAX_USERS", "40"))
        spawn_rate = int(os.getenv("LOADTEST_SPAWN_RATE", "4"))
        if elapsed < self.ramp_seconds:
            users = max(1, round(max_users * elapsed / self.ramp_seconds))
        elif elapsed < self.ramp_seconds + self.hold_seconds:
            users = max_users
        elif elapsed < self.ramp_seconds + self.hold_seconds + self.down_seconds:
            remaining = 1.0 - ((elapsed - self.ramp_seconds - self.hold_seconds) / self.down_seconds)
            users = max(0, round(max_users * remaining))
        else:
            return None
        return users, spawn_rate
