import requests


class CanvasClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, params: dict | None = None) -> requests.Response:
        return self.session.get(
            f"{self.base_url}/api/v1{path}", params=params, timeout=30
        )

    def get_paginated(self, path: str, params: dict | None = None):
        url = f"{self.base_url}/api/v1{path}"
        while url:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            yield from response.json()
            url = response.links.get("next", {}).get("url")
            params = None
