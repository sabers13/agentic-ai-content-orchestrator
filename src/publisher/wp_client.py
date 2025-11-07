# src/publisher/wp_client.py
from __future__ import annotations

import re
import requests
from requests import RequestException

from src.common.config import settings


class WordPressDotComClient:
    REQUEST_TIMEOUT = 15

    def __init__(self):
        api_base = settings.WP_DOTCOM_API_BASE
        token = settings.WP_DOTCOM_BEARER

        if not api_base:
            raise RuntimeError("WP_DOTCOM_API_BASE is not configured; check your .env file.")
        if not token:
            raise RuntimeError("WP_DOTCOM_BEARER is not configured; check your .env file.")

        self.api_base = api_base.rstrip("/")
        self.token = token

    def create_post(
        self,
        title: str,
        content: str,
        slug: str | None = None,
        status: str = "publish",
        tags=None,
        categories=None,
        excerpt: str | None = None,
    ):
        url = f"{self.api_base}/posts"
        payload: dict[str, object] = {
            "title": title,
            "status": status,
        }
        payload["content"] = {"raw": content}
        if excerpt:
            payload["excerpt"] = {"raw": excerpt}
        if slug:
            payload["slug"] = slug
        if tags:
            payload["tags"] = self._resolve_terms(tags, "tags")
        if categories:
            payload["categories"] = self._resolve_terms(categories, "categories")

        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            raise RuntimeError(f"WP.com publish request failed: {exc}") from exc

        if not resp.ok:
            raise RuntimeError(f"WP.com publish failed: {resp.status_code} {resp.text}")
        try:
            return resp.json()
        except ValueError as exc:
            raise RuntimeError(
                f"WP.com returned non-JSON response ({resp.status_code}): {resp.text[:500]}"
            ) from exc

    def _resolve_terms(self, terms, taxonomy: str) -> list[int]:
        """
        Convert provided tags/categories into numeric IDs, creating new terms if needed.
        Accepts integers (returned as-is) and strings (treated as names).
        """
        resolved: list[int] = []
        if not isinstance(terms, (list, tuple, set)):
            terms = [terms]

        for term in terms:
            if isinstance(term, int):
                resolved.append(term)
                continue

            if not isinstance(term, str):
                print(f"[publisher] Skipping unsupported term value for {taxonomy}: {term}")
                continue

            term_id = self._ensure_term(taxonomy, term.strip())
            if term_id is not None:
                resolved.append(term_id)
            else:
                print(f"[publisher] Warning: could not resolve {taxonomy[:-1]} '{term}'")

        return resolved

    def _ensure_term(self, taxonomy: str, name: str) -> int | None:
        existing = self._find_term(taxonomy, name)
        if existing is not None:
            return existing
        return self._create_term(taxonomy, name)

    def _find_term(self, taxonomy: str, name: str) -> int | None:
        slug = self._slugify(name)
        params = {"per_page": 100, "search": name}
        if slug:
            params["slug"] = slug
        try:
            resp = requests.get(
                f"{self.api_base}/{taxonomy}",
                headers=self._headers(),
                params=params,
                timeout=self.REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            print(f"[publisher] Failed to search {taxonomy}: {exc}")
            return None

        if not resp.ok:
            print(f"[publisher] Failed to search {taxonomy}: {resp.status_code} {resp.text}")
            return None

        for term in resp.json():
            term_name = term.get("name", "")
            if isinstance(term_name, str) and term_name.lower() == name.lower():
                return term.get("id")
            term_slug = term.get("slug", "")
            if isinstance(term_slug, str) and slug and term_slug == slug:
                return term.get("id")
        return None

    def _create_term(self, taxonomy: str, name: str) -> int | None:
        payload = {"name": name}
        slug = self._slugify(name)
        if slug:
            payload["slug"] = slug
        try:
            resp = requests.post(
                f"{self.api_base}/{taxonomy}",
                headers=self._headers(),
                json=payload,
                timeout=self.REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            print(f"[publisher] Failed to create {taxonomy[:-1]} '{name}': {exc}")
            return None

        if resp.status_code == 400 and "term_exists" in resp.text:
            # Race: term created concurrently. Retry lookup.
            return self._find_term(taxonomy, name)

        if not resp.ok:
            print(
                f"[publisher] Failed to create {taxonomy[:-1]} '{name}': "
                f"{resp.status_code} {resp.text}"
            )
            return None

        data = resp.json()
        return data.get("id")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
        return slug.strip("-")
