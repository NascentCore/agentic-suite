"""Session management — multi-turn conversational state with checkpoint/resume.

Each ``RuntimeSession`` tracks the user's interaction history with a running
application.  The ``SessionManager`` provides CRUD and checkpoint/resume
semantics so that long-running conversations can survive agent restarts.
"""

from __future__ import annotations

from typing import Any

from .models import (
    ActionRequest,
    ActionResponse,
    RuntimeSession,
    _new_id,
    _utc_now,
)


class SessionManager:
    """In-memory session store with checkpoint/resume support."""

    def __init__(self) -> None:
        self._sessions: dict[str, RuntimeSession] = {}

    # -- CRUD ---------------------------------------------------------------

    def create(self, user_did: str, app_name: str) -> RuntimeSession:
        """Start a new conversational session."""
        session = RuntimeSession(
            session_id=_new_id(),
            user_did=user_did,
            app_name=app_name,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> RuntimeSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self, user_did: str | None = None) -> list[RuntimeSession]:
        sessions = list(self._sessions.values())
        if user_did:
            sessions = [s for s in sessions if s.user_did == user_did]
        return sorted(sessions, key=lambda s: s.last_active, reverse=True)

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    # -- history tracking ---------------------------------------------------

    def record_request(self, session_id: str, request: ActionRequest) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        session.history.append({"type": "request", **request.model_dump(mode="json")})
        session.last_active = _utc_now()

    def record_response(self, session_id: str, response: ActionResponse) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        session.history.append({"type": "response", **response.model_dump(mode="json")})
        session.last_active = _utc_now()

    def update_context(self, session_id: str, key: str, value: Any) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        session.context[key] = value
        session.last_active = _utc_now()

    # -- checkpoint / resume ------------------------------------------------

    def checkpoint(self, session_id: str) -> str:
        """Snapshot current session state and return a checkpoint token."""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        token = _new_id()
        session.checkpoint = token
        session.last_active = _utc_now()
        return token

    def resume(self, session_id: str, checkpoint_token: str) -> RuntimeSession:
        """Verify checkpoint token and return the session for continued use."""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        if session.checkpoint != checkpoint_token:
            raise ValueError("Checkpoint token mismatch.")
        session.last_active = _utc_now()
        return session

    # -- export (for persistence / migration) --------------------------------

    def export_session(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
        return session.model_dump(mode="json")

    def import_session(self, data: dict[str, Any]) -> RuntimeSession:
        session = RuntimeSession.model_validate(data)
        self._sessions[session.session_id] = session
        return session
