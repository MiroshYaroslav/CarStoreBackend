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
    def list_default(self):
        self.client.get("/api/v1/products/", name="GET products")

    @task(1)
    def list_search(self):
        self.client.get("/api/v1/products/?search=BMW", name="GET products search")

    @task(1)
    def list_min_price(self):
        self.client.get("/api/v1/products/?min_price=10000", name="GET products min price")

    @task(1)
    def list_price_range(self):
        self.client.get(
            "/api/v1/products/?min_price=10000&max_price=150000",
            name="GET products price range",
        )

    @task(1)
    def list_sort_asc(self):
        self.client.get("/api/v1/products/?sort=price-asc", name="GET products sort asc")

    @task(1)
    def list_sort_desc(self):
        self.client.get("/api/v1/products/?sort=price-desc", name="GET products sort desc")

    @task(1)
    def list_search_sorted(self):
        self.client.get(
            "/api/v1/products/?search=BMW&sort=price_asc",
            name="GET products search and sort",
        )

    @task(1)
    def list_by_category(self):
        categories = type(self).categories
        if categories:
            category_id = random.choice(categories)["id"]
            self.client.get(
                f"/api/v1/products/?category_id={category_id}",
                name="GET products category",
            )
        else:
            self.client.get("/api/v1/products/", name="GET products category fallback")

    @task(1)
    def list_inactive_included(self):
        self.client.get(
            "/api/v1/products/?active_only=false", name="GET products include inactive"
        )

    @task(1)
    def product_detail(self):
        products = type(self).products
        if products:
            product_id = random.choice(products)["id"]
            self.client.get(
                f"/api/v1/products/{product_id}", name="GET product detail"
            )
        else:
            self.client.get("/api/v1/products/", name="GET products detail fallback")

    @task(1)
    def create_test_write(self):
        """Exercise one real write endpoint; callback requests need no auth."""
        suffix = uuid.uuid4().hex[:10]
        self.client.post(
            "/api/v1/callback-requests/",
            json={
                "name": "Load test",
                "phone": f"+38099{random.randint(1000000, 9999999)}",
                "description": f"Automated load test {suffix}",
            },
            name="POST callback request (write)",
        )


class CatalogLoadShape(LoadTestShape):
    """Ramp up for 2.5m, hold 5m, then ramp down for 2m."""

    ramp_seconds = 150
    hold_seconds = 300
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
            remaining = 1 - (elapsed - self.ramp_seconds - self.hold_seconds) / self.down_seconds
            users = max(0, round(max_users * remaining))
        else:
            return None
        return users, spawn_rate
