"""Tests for agentic_runtime.session — session management."""

from __future__ import annotations

import pytest

from agentic_runtime.models import ActionRequest, ActionResponse
from agentic_runtime.session import SessionManager


class TestSessionManager:
    def test_create_and_get(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "test-app")
        assert session.user_did == "did:plc:alice"
        assert session.app_name == "test-app"
        fetched = mgr.get(session.session_id)
        assert fetched is not None
        assert fetched.session_id == session.session_id

    def test_list_sessions(self) -> None:
        mgr = SessionManager()
        mgr.create("did:plc:alice", "app1")
        mgr.create("did:plc:bob", "app2")
        mgr.create("did:plc:alice", "app3")
        assert len(mgr.list_sessions()) == 3
        assert len(mgr.list_sessions(user_did="did:plc:alice")) == 2

    def test_delete(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "app")
        assert mgr.delete(session.session_id) is True
        assert mgr.get(session.session_id) is None
        assert mgr.delete(session.session_id) is False

    def test_record_request_and_response(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "app")
        req = ActionRequest(tool_id="t1", parameters={"q": "hi"})
        resp = ActionResponse(request_id=req.request_id, status="success", result={"data": "ok"})

        mgr.record_request(session.session_id, req)
        mgr.record_response(session.session_id, resp)

        updated = mgr.get(session.session_id)
        assert len(updated.history) == 2
        assert updated.history[0]["type"] == "request"
        assert updated.history[1]["type"] == "response"

    def test_update_context(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "app")
        mgr.update_context(session.session_id, "last_tool", "list_users")
        updated = mgr.get(session.session_id)
        assert updated.context["last_tool"] == "list_users"

    def test_checkpoint_and_resume(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "app")
        token = mgr.checkpoint(session.session_id)
        resumed = mgr.resume(session.session_id, token)
        assert resumed.session_id == session.session_id

    def test_resume_wrong_token(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "app")
        mgr.checkpoint(session.session_id)
        with pytest.raises(ValueError, match="mismatch"):
            mgr.resume(session.session_id, "wrong-token")

    def test_missing_session_raises(self) -> None:
        mgr = SessionManager()
        with pytest.raises(KeyError):
            mgr.record_request("nonexistent", ActionRequest(tool_id="t1"))
        with pytest.raises(KeyError):
            mgr.checkpoint("nonexistent")

    def test_export_import(self) -> None:
        mgr = SessionManager()
        session = mgr.create("did:plc:alice", "app")
        mgr.update_context(session.session_id, "key", "value")

        exported = mgr.export_session(session.session_id)
        mgr.delete(session.session_id)

        imported = mgr.import_session(exported)
        assert imported.session_id == session.session_id
        assert imported.context["key"] == "value"
