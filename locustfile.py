import uuid
from locust import HttpUser, task, between


class ShortenerUser(HttpUser):
    wait_time = between(
        0.01, 0.1  # <-- the test is being sent every 10-100ms , make your mind for dey
    )  # near-continuous — this is a stress test (like they do with concrete lol)

    def on_start(self):
        self.email = f"loadtest_{uuid.uuid4()}@test.com"  # <-- unique ID's so we dont just test caching
        self.password = "testpass123"

        self.client.post(
            "/register",  # <-- hits /register to create the account in the database because thats the real work in my shi
            json={
                "email": self.email,
                "password": self.password,
            },
        )

        resp = self.client.post(
            "/login",  # <-- hits /login to generate a real JWT access_token
            data={
                "username": self.email,
                "password": self.password,
            },
        )
        token = resp.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {token}"
        }  # <-- SAVED so all future work doesn't need re-auth

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
