# src/publisher/wp_dotcom_client.py
import json

import requests
from requests import RequestException

from src.common.config import settings


class WordPressDotComClient:
    REQUEST_TIMEOUT = 10

    def __init__(self):
        if not settings.WP_DOTCOM_API_BASE:
            raise ValueError("WP_DOTCOM_API_BASE is not set")
        self.base_url = settings.WP_DOTCOM_API_BASE.rstrip("/")
        self.token = settings.WP_DOTCOM_BEARER

    def _headers(self):
        headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def ping(self):
        # simple GET to make sure site is reachable
        resp = requests.get(
            f"{self.base_url}/posts",
            headers=self._headers(),
            timeout=self.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def debug_token(self):
        print("== Debugging WordPress.com token ==")
        if not self.token:
            print("WP_DOTCOM_BEARER is not configured. Set it in your environment.")
            return

        endpoints = [
            ("Profile", "https://public-api.wordpress.com/rest/v1.1/me"),
            ("Sites", "https://public-api.wordpress.com/rest/v1.1/me/sites"),
        ]
        sites_payload = None

        for label, url in endpoints:
            try:
                resp = requests.get(
                    url,
                    headers=self._headers(),
                    timeout=self.REQUEST_TIMEOUT,
                )
            except RequestException as exc:
                print(f"[{label}] request failed: {exc}")
                continue

            print(f"[{label}] status={resp.status_code}")
            payload = self._safe_json(resp)
            print(self._format_payload(payload))

            if label == "Sites" and isinstance(payload, dict):
                sites_payload = payload

        target_site = getattr(settings, "WP_DOTCOM_SITE", None)
        if not target_site:
            return

        if not self._token_has_site_access(target_site, sites_payload):
            print(
                "Your current token is not authorized for "
                f"{target_site}. Re-authorize the app in "
                "https://developer.wordpress.com/apps/ with write permissions "
                "and generate a new token."
            )
        else:
            print(f"Token appears to include access to {target_site}.")

    def create_draft_post(self, title: str, content: str, slug: str | None = None):
        payload = {
            "title": title,
            "content": content,
            "status": "draft",
        }
        if slug:
            payload["slug"] = slug

        try:
            resp = requests.post(
                f"{self.base_url}/posts",
                headers=self._headers(),
                json=payload,
                timeout=self.REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            raise Exception(f"WP.com POST request failed: {exc}") from exc

        if resp.status_code >= 400:
            body = self._safe_json(resp)
            raise Exception(f"WP.com POST failed: {resp.status_code} {body}")
        return resp.json()

    def create_draft_raw(self, payload: dict):
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")

        try:
            resp = requests.post(
                f"{self.base_url}/posts",
                headers=self._headers(),
                json=payload,
                timeout=self.REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            print(f"[create_draft_raw] request failed: {exc}")
            return None

        print(f"[create_draft_raw] status={resp.status_code}")
        body = self._safe_json(resp)
        print(self._format_payload(body))
        return body

    def _token_has_site_access(self, target_site: str, sites_payload: dict | None):
        if not sites_payload or not isinstance(sites_payload, dict):
            return False

        sites = sites_payload.get("sites") or []
        if not isinstance(sites, list):
            return False

        target_normalized = self._normalize_site(target_site)
        for site in sites:
            if not isinstance(site, dict):
                continue

            url = site.get("URL") or site.get("url")
            slug = site.get("slug")

            if url and self._normalize_site(url) == target_normalized:
                return True
            if slug and self._normalize_site(slug) == target_normalized:
                return True

        return False

    @staticmethod
    def _normalize_site(value: str):
        normalized = value.lower()
        for prefix in ("https://", "http://"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        return normalized.rstrip("/")

    @staticmethod
    def _safe_json(resp: requests.Response):
        try:
            return resp.json()
        except ValueError:
            return resp.text

    @staticmethod
    def _format_payload(payload):
        if isinstance(payload, (dict, list)):
            return json.dumps(payload, indent=2, sort_keys=True)
        return payload


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    client = WordPressDotComClient()
    client.debug_token()

    try:
        draft = client.create_draft_post(
            "Agentic Orchestrator Debug Post",
            "<p>This is a debug draft generated by the wp_dotcom_client script.</p>",
            slug="agentic-orchestrator-debug",
        )
        print("[create_draft_post] success")
        print(json.dumps(draft, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"[create_draft_post] failed: {exc}")
