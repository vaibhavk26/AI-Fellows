import os
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class ApiError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _message(response: requests.Response) -> str:
    try:
        payload = response.json()
        detail = payload.get("detail", payload)
        if isinstance(detail, dict):
            return detail.get("message") or detail.get("code") or str(detail)
        return str(detail)
    except ValueError:
        return response.text or f"Request failed with status {response.status_code}"


def request(method: str, path: str, **kwargs: Any) -> dict:
    headers = kwargs.pop("headers", {}).copy()
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", headers=headers, timeout=90, **kwargs)
    except requests.RequestException as error:
        raise ApiError(0, f"Backend unavailable at {API_BASE_URL}: {error}") from error
    if not response.ok:
        raise ApiError(response.status_code, _message(response))
    if response.status_code == 204 or not response.content:
        return {}
    return response.json()


def get(path: str, **kwargs: Any) -> dict:
    return request("GET", path, **kwargs)


def post(path: str, **kwargs: Any) -> dict:
    return request("POST", path, **kwargs)


def clear_session() -> None:
    for key in ("access_token", "user", "active_exam", "active_attempt", "last_result"):
        st.session_state.pop(key, None)


def require_auth(role: str | None = None) -> bool:
    user = st.session_state.get("user")
    if not user:
        st.warning("Sign in from the home page to continue.")
        return False
    if role and user.get("role") != role:
        st.error("This page is available only to teachers." if role == "teacher" else "This page is available only to students.")
        return False
    return True


def options_for(items: list[dict], label_key: str = "name") -> dict[str, dict]:
    return {item[label_key]: item for item in items}
