import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

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
    token = kwargs.pop("access_token", None) or st.session_state.get("access_token")
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


@st.cache_data(ttl=300, show_spinner=False)
def get_subjects() -> list[dict]:
    return get("/api/v1/curriculum/subjects", params={"page_size": 100}).get("data", [])


@st.cache_data(ttl=300, show_spinner=False)
def get_chapters_for_subject(subject_id: str) -> list[dict]:
    return _load_chapters_for_subject(subject_id, access_token=st.session_state.get("access_token"))


def _load_chapters_for_subject(subject_id: str, access_token: str | None = None) -> list[dict]:
    if not subject_id:
        return []
    return get(
        f"/api/v1/curriculum/subjects/{subject_id}/chapters",
        params={"page_size": 100},
        access_token=access_token,
    ).get("data", [])


@st.cache_data(ttl=300, show_spinner=False)
def get_topics_for_chapter(chapter_id: str) -> list[dict]:
    return _load_topics_for_chapter(chapter_id, access_token=st.session_state.get("access_token"))


def _load_topics_for_chapter(chapter_id: str, access_token: str | None = None) -> list[dict]:
    if not chapter_id:
        return []
    return get(
        f"/api/v1/curriculum/chapters/{chapter_id}/topics",
        params={"page_size": 100},
        access_token=access_token,
    ).get("data", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_student_attempts() -> list[dict]:
    return get("/api/v1/students/me/attempts", params={"status": "submitted", "page_size": 20}).get("data", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_attempt_detail(attempt_id: str) -> dict:
    return get(f"/api/v1/attempts/{attempt_id}")["data"]


@st.cache_data(ttl=60, show_spinner=False)
def get_teacher_dashboard() -> dict:
    return get("/api/v1/teachers/me/dashboard")["data"]


@st.cache_data(ttl=60, show_spinner=False)
def get_teacher_questions() -> list[dict]:
    return get("/api/v1/questions", params={"page_size": 100}).get("data", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_student_progress() -> dict:
    return get("/api/v1/students/me/progress", params={"page_size": 100})


def get_student_analytics(params: dict | None = None) -> dict:
    return get("/api/v1/students/me/analytics", params=params or {})


@st.cache_data(ttl=60, show_spinner=False)
def get_weak_topics() -> dict:
    return get("/api/v1/students/me/weak-topics", params={"page_size": 100})


def _start_background_load(key: str, loader: Callable[..., Any], *args: Any) -> Future:
    executor = st.session_state.setdefault("_background_executor", ThreadPoolExecutor(max_workers=8))
    previous = st.session_state.get(key)
    if isinstance(previous, Future) and not previous.done():
        return previous
    access_token = st.session_state.get("access_token")
    future = executor.submit(loader, *args, access_token=access_token)
    st.session_state[key] = future
    return future


def _background_result(future: Future, loading_message: str) -> Any:
    if not future.done():
        st.info(loading_message)
        time.sleep(0.1)
        st.rerun()
    return future.result()


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
