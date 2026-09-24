import uuid
from locust import HttpUser, task, between


class ShortenerUser(HttpUser):
    wait_time = between(0.01, 0.1)  # near-continuous — this is a stress test

    def on_start(self):
        self.email = f"loadtest_{uuid.uuid4()}@test.com"
        self.password = "testpass123"

        self.client.post(
            "/register",
            json={
                "email": self.email,
                "password": self.password,
            },
        )

        resp = self.client.post(
            "/login",
            data={
                "username": self.email,
                "password": self.password,
            },
        )
        token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {token}"}

    @task
    def shorten_url(self):
        # unique URL every call since using the same shorten() logic returns cached data
        # short_code repeating the URL from the same user, without writing to DB
        unique_url = f"https://example.com/{uuid.uuid4()}"
        self.client.post(
            "/shorten_url",
            json={"username": self.email, "long_url": unique_url},
            headers=self.headers,
        )
