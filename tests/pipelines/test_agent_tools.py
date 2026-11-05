"""External tools: contracts, read-only session, timeout, fallback, routing, trace.

No HealthCore API here: HTTP is either ``httpx.MockTransport`` or a local socket
that accepts and never answers. The same tools are exercised against the real
API routes in ``services/api/tests/test_agent_tools_live_api.py``.
"""

from __future__ import annotations

import inspect
import json
import socket
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.knowledge_agent import AgentDependencies, AgentRunner, SourcePlanner, rules_plan  # noqa: E402
from services.knowledge_agent.planner import extract_ticket_id, plan_from_llm_reply  # noqa: E402
from services.knowledge_agent.tools import (  # noqa: E402
    TOOL_TIMEOUT_SECONDS,
    InventoryLookupInput,
    InventoryLookupTool,
    ReadOnlyApiSession,
    ReadOnlyViolation,
    ServiceCredentials,
    TicketLookupInput,
    TicketLookupTool,
)
from services.knowledge_agent.tools import incidents as incidents_module  # noqa: E402
from services.knowledge_agent.tools import inventory as inventory_module  # noqa: E402
from services.knowledge_agent.tools import session as session_module  # noqa: E402

CREDS = ServiceCredentials(base_url="http://api.test", email="agent@healthcore.example", password="pw")
INC_0042 = {
    "incident_id": "INC-0042",
    "clinic_id": "us-tx-002",
    "country": "US",
    "category": "WORKFORCE",
    "status": "closed",
    "satisfaction_score": 3.5,
    "source_file": "incidents-healthcore.csv",
    "first_recorded_at": "2026-11-04T10:00:00+00:00",
    "updated_at": "2026-11-04T10:00:00+00:00",
}
PRODUCTS = [
    {"id": 1, "name": "Nitrile exam gloves (box of 100)", "sku": "PPE-GLV-100", "threshold": 20, "current_stock": 12, "category": "ppe"},
    {"id": 2, "name": "Surgical masks (box of 50)", "sku": "PPE-MSK-050", "threshold": 10, "current_stock": 40, "category": "ppe"},
]
STATUS_WORDS = ("is open", "is closed", "is discarded", " in stock,")


class FakeApi:
    """Records every request; answers like the HealthCore API unless told otherwise."""

    def __init__(self, **overrides: Any) -> None:
        self.requests: list[httpx.Request] = []
        self.overrides = overrides
        self.login_failures = overrides.get("expire_first_token", 0)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path == "/auth/login":
            if self.overrides.get("login_status"):
                return httpx.Response(self.overrides["login_status"], json={"detail": "no"})
            return httpx.Response(200, json={"access_token": f"tok{len(self.requests)}", "token_type": "bearer"})
        if self.login_failures and request.headers["Authorization"] == "Bearer tok1":
            self.login_failures -= 1
            return httpx.Response(401, json={"detail": "expired"})
        if "status" in self.overrides:
            return httpx.Response(self.overrides["status"], json={"detail": "x"})
        if self.overrides.get("not_json"):
            return httpx.Response(200, text="<html>proxy</html>")
        if path == "/api/incidents/INC-0042":
            return httpx.Response(200, json=INC_0042)
        if path.startswith("/api/incidents/"):
            return httpx.Response(404, json={"detail": "Incident not found."})
        if path == "/api/incidents":
            return httpx.Response(200, json={"total": 6, "items": [INC_0042 | {"status": "open", "category": "BILLING"}] * 5})
        if path == "/inventory/products":
            return httpx.Response(200, json=PRODUCTS)
        return httpx.Response(404, json={"detail": "Not Found"})

    def session(self, timeout_seconds: float = TOOL_TIMEOUT_SECONDS) -> ReadOnlyApiSession:
        client = httpx.Client(transport=httpx.MockTransport(self.handler), base_url=CREDS.base_url)
        return ReadOnlyApiSession(CREDS, client=client, timeout_seconds=timeout_seconds)


# ---------------------------------------------------------------------------
# Typed contracts
# ---------------------------------------------------------------------------


def test_ticket_input_needs_an_id_or_a_filter_and_rejects_unknown_fields() -> None:
    assert TicketLookupInput(ticket_id="INC-0042").ticket_id == "INC-0042"
    assert TicketLookupInput(status="open", category="BILLING").limit == 5
    for bad in ({}, {"ticket_id": "482"}, {"status": "pending"}, {"ticket_id": "INC-0042", "patient_id": "PAT-1"}):
        with pytest.raises(ValidationError):
            TicketLookupInput.model_validate(bad)
    with pytest.raises(ValidationError):
        InventoryLookupInput(product_query="x")


# ---------------------------------------------------------------------------
# Timeout and read-only guarantees
# ---------------------------------------------------------------------------


def test_timeout_is_an_explicit_four_seconds_sent_on_every_request() -> None:
    api = FakeApi()
    TicketLookupTool(api.session())(TicketLookupInput(ticket_id="INC-0042"))

    assert TOOL_TIMEOUT_SECONDS == 4.0
    assert ReadOnlyApiSession(CREDS, client=httpx.Client()).timeout_seconds == 4.0
    for request in api.requests:
        timeouts = request.extensions["timeout"]
        assert 0 < timeouts["read"] <= 4.0 and 0 < timeouts["connect"] <= 4.0


@pytest.fixture
def silent_server():
    """Accepts TCP connections and never sends a byte — a hung incident service."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept() -> None:
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                held.append(server.accept()[0])
            except OSError:
                continue

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.getsockname()[1]}"
    stop.set()
    thread.join(1)
    for conn in held:
        conn.close()
    server.close()


def test_hung_service_times_out_at_four_seconds_and_never_hangs(silent_server: str) -> None:
    tool = TicketLookupTool(ReadOnlyApiSession(ServiceCredentials(silent_server, "a@b.example", "pw")))

    started = time.perf_counter()
    output = tool(TicketLookupInput(ticket_id="INC-0042"))
    elapsed = time.perf_counter() - started

    assert output.status == "timeout"
    assert output.tickets == ()
    assert 3.9 <= elapsed < 5.0


def test_unreachable_service_is_unavailable() -> None:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    closed_port = probe.getsockname()[1]
    probe.close()
    tool = TicketLookupTool(ReadOnlyApiSession(ServiceCredentials(f"http://127.0.0.1:{closed_port}", "a@b.example", "pw")))

    assert tool(TicketLookupInput(ticket_id="INC-0042")).status == "unavailable"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_session_refuses_any_write(method: str) -> None:
    api = FakeApi()
    session = api.session()

    with pytest.raises(ReadOnlyViolation):
        session._send(method, "/api/incidents/INC-0042", time.monotonic() + 4)
    with pytest.raises(ReadOnlyViolation):
        session._send(method, "/inventory/products", time.monotonic() + 4)
    assert api.requests == []


def test_tools_only_issue_get_requests_besides_the_token_login() -> None:
    api = FakeApi()
    session = api.session()
    TicketLookupTool(session)(TicketLookupInput(ticket_id="INC-0042"))
    TicketLookupTool(session)(TicketLookupInput(status="open"))
    InventoryLookupTool(session)(InventoryLookupInput(product_query="gloves"))

    assert [(r.method, r.url.path) for r in api.requests] == [
        ("POST", "/auth/login"),
        ("GET", "/api/incidents/INC-0042"),
        ("GET", "/api/incidents"),
        ("GET", "/inventory/products"),
    ]
    for module in (incidents_module, inventory_module, session_module):
        source = inspect.getsource(module)
        for write_call in (".post(", ".put(", ".patch(", ".delete("):
            assert write_call not in source


def test_each_tool_has_a_single_responsibility() -> None:
    ticket_api, inventory_api = FakeApi(), FakeApi()
    TicketLookupTool(ticket_api.session())(TicketLookupInput(ticket_id="INC-0042"))
    InventoryLookupTool(inventory_api.session())(InventoryLookupInput(product_query="gloves"))

    assert {r.url.path for r in ticket_api.requests} - {"/auth/login"} == {"/api/incidents/INC-0042"}
    assert {r.url.path for r in inventory_api.requests} - {"/auth/login"} == {"/inventory/products"}
    assert "inventory" not in inspect.getsource(incidents_module).lower()
    assert "incident" not in inspect.getsource(inventory_module).lower()


# ---------------------------------------------------------------------------
# Auth and failure mapping
# ---------------------------------------------------------------------------


def test_bearer_token_from_service_login_is_sent_and_refreshed_once_on_401() -> None:
    api = FakeApi(expire_first_token=1)
    output = TicketLookupTool(api.session())(TicketLookupInput(ticket_id="INC-0042"))

    assert output.status == "ok"
    assert json.loads(api.requests[0].content) == {"email": CREDS.email, "password": CREDS.password}
    assert [r.headers.get("Authorization") for r in api.requests if r.method == "GET"] == ["Bearer tok1", "Bearer tok3"]


def test_credentials_come_from_env_and_missing_ones_never_call_the_service(monkeypatch) -> None:
    monkeypatch.delenv("AGENT_SERVICE_EMAIL", raising=False)
    monkeypatch.delenv("AGENT_SERVICE_PASSWORD", raising=False)
    assert ServiceCredentials.from_env() is None
    assert TicketLookupTool.from_env()(TicketLookupInput(ticket_id="INC-0042")).status == "auth_failed"

    monkeypatch.setenv("AGENT_SERVICE_EMAIL", "agent@healthcore.example")
    monkeypatch.setenv("AGENT_SERVICE_PASSWORD", "from-env")
    monkeypatch.setenv("HEALTHCORE_API_URL", "http://api.internal:8001/")
    assert ServiceCredentials.from_env() == ServiceCredentials("http://api.internal:8001", "agent@healthcore.example", "from-env")


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"login_status": 401}, "auth_failed"),
        ({"status": 403}, "auth_failed"),
        ({"status": 500}, "unavailable"),
        ({"status": 503}, "unavailable"),
        ({"not_json": True}, "bad_response"),
    ],
)
def test_service_failures_map_to_a_status_instead_of_raising(overrides: dict, expected: str) -> None:
    output = TicketLookupTool(FakeApi(**overrides).session())(TicketLookupInput(ticket_id="INC-0042"))
    assert output.status == expected and output.tickets == ()


def test_ticket_lookup_returns_typed_records_from_the_service() -> None:
    api = FakeApi()
    one = TicketLookupTool(api.session())(TicketLookupInput(ticket_id="INC-0042"))
    missing = TicketLookupTool(api.session())(TicketLookupInput(ticket_id="INC-0482"))
    search = TicketLookupTool(api.session())(TicketLookupInput(status="open", category="BILLING"))

    assert (one.status, one.total, one.tickets[0].status, one.http_status) == ("ok", 1, "closed", 200)
    assert one.endpoint == "/api/incidents/INC-0042"
    assert (missing.status, missing.http_status) == ("not_found", 404)
    assert (search.status, search.total, len(search.tickets)) == ("ok", 6, 5)
    assert search.endpoint == "/api/incidents?status=open&category=BILLING&limit=5"


def test_inventory_lookup_matches_by_name_or_sku_and_flags_low_stock() -> None:
    tool = InventoryLookupTool(FakeApi().session())

    gloves = tool(InventoryLookupInput(product_query="nitrile exam gloves"))
    by_sku = tool(InventoryLookupInput(product_query="ppe-msk-050"))
    unknown = tool(InventoryLookupInput(product_query="MRI contrast agent"))

    assert gloves.status == "ok"
    assert [(p.sku, p.current_stock, p.below_threshold) for p in gloves.products] == [("PPE-GLV-100", 12, True)]
    assert [p.sku for p in by_sku.products] == ["PPE-MSK-050"]
    assert (unknown.status, unknown.products) == ("not_found", ())


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("question", "sources", "ticket_input"),
    [
        ("What's the status of ticket INC-0042?", ["ticket"], {"ticket_id": "INC-0042"}),
        ("what's the status of ticket 482?", ["ticket"], {"ticket_id": "INC-0482"}),
        ("Can you check incident #63 for me?", ["ticket"], {"ticket_id": "INC-0063"}),
        ("How many open billing incidents do we have right now?", ["ticket"], {"status": "open", "category": "BILLING"}),
        ("Do we have stock of nitrile exam gloves?", ["inventory"], None),
        ("Do Medicare patients pay a no-show fee?", ["knowledge_base"], None),
        ("Is there a charge for cancelling 12 hours in advance?", ["knowledge_base"], None),
        ("A patient has had no referral appointment options for 5 business days. Who do I escalate to?", ["knowledge_base"], None),
        ("What is the Wi-Fi password for the staff network?", ["knowledge_base"], None),
        (
            "Ticket INC-0007 is about a cancelled appointment. What is its status, and what is our cancellation fee?",
            ["ticket", "knowledge_base"],
            {"ticket_id": "INC-0007"},
        ),
    ],
)
def test_rules_planner_routes_by_question_content(question: str, sources: list[str], ticket_input: dict | None) -> None:
    plan = rules_plan(question)
    assert plan["sources"] == sources
    assert plan["ticket_input"] == ticket_input
    assert plan["planner"] == "rules"


def test_rules_planner_extracts_the_product_name() -> None:
    assert rules_plan("Do we have stock of nitrile exam gloves?")["inventory_input"] == {"product_query": "nitrile exam gloves"}
    assert rules_plan("How many surgical masks are left in stock?")["inventory_input"] == {"product_query": "surgical masks"}


def test_ticket_ids_are_normalised_and_never_guessed() -> None:
    assert extract_ticket_id("ticket 7") == "INC-0007"
    assert extract_ticket_id("INC-0042 please") == "INC-0042"
    assert extract_ticket_id("cancelling 12 hours in advance") is None


def test_llm_plan_is_validated_and_ticket_id_is_grounded_in_the_question() -> None:
    reply = '```json\n{"sources": ["ticket"], "ticket": {"ticket_id": "INC-9999"}, "inventory": null}\n```'
    plan = plan_from_llm_reply("what's the status of ticket 482?", reply)
    invented = plan_from_llm_reply("what's the status of my ticket?", reply)

    assert plan == {
        "sources": ["ticket"],
        "ticket_input": {"ticket_id": "INC-0482"},
        "inventory_input": None,
        "knowledge_question": None,
        "planner": "llm",
    }
    assert invented["ticket_input"] == {}


def test_mixed_question_sends_only_the_policy_part_to_the_knowledge_base() -> None:
    question = (
        "Ticket INC-0007 is about a late cancellation. What is its status, "
        "and what fee do we charge for cancelling less than 24 hours ahead?"
    )
    assert rules_plan(question)["knowledge_question"] == "What fee do we charge for cancelling less than 24 hours ahead?"
    assert rules_plan("Do Medicare patients pay a no-show fee?")["knowledge_question"] is None


class StubLlm:
    def __init__(self, reply: str | None = None, error: Exception | None = None) -> None:
        self.reply, self.error, self.calls, self.options = reply, error, [], {}
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def with_options(self, **options: Any) -> StubLlm:
        self.options.update(options)
        return self

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.reply))])


def test_llm_planner_orders_sources_and_has_its_own_timeout() -> None:
    llm = StubLlm('{"sources": ["knowledge_base", "ticket"], "ticket": {"ticket_id": "INC-0007"}}')
    plan = SourcePlanner(llm_client=llm, model="m")("INC-0007 status and the cancellation fee?")

    assert plan["sources"] == ["ticket", "knowledge_base"] and plan["planner"] == "llm"
    assert llm.calls[0]["timeout"] == 8.0 and llm.calls[0]["temperature"] == 0
    assert llm.options == {"max_retries": 1}


@pytest.mark.parametrize("llm", [StubLlm("I think you need the ticket tool."), StubLlm('{"sources": []}'), StubLlm(error=TimeoutError())])
def test_llm_planner_failure_falls_back_to_rules(llm: StubLlm) -> None:
    plan = SourcePlanner(llm_client=llm, model="m")("What's the status of ticket 482?")
    assert plan == {
        "sources": ["ticket"],
        "ticket_input": {"ticket_id": "INC-0482"},
        "inventory_input": None,
        "knowledge_question": None,
        "planner": "rules_fallback",
    }


# ---------------------------------------------------------------------------
# Graph: routing, fallback path, order, trace
# ---------------------------------------------------------------------------


CHUNK = {"source_document": "appointment-policy", "chunk_index": 1, "section": "Cancellation policy", "text": "50 USD", "score": 0.6}
rag_questions: list[str] = []


@pytest.fixture
def make_runner(tmp_path: Path):
    runners: list[AgentRunner] = []

    def _make(api: FakeApi, *, store_text: bool = False, hits: list | None = None) -> AgentRunner:
        session = api.session()
        rag_questions.clear()

        def retrieve(q: str) -> list:
            rag_questions.append(q)
            return [CHUNK] if hits is None else hits

        deps = AgentDependencies(
            retrieve=retrieve,
            generate_answer=lambda q, c: rag_questions.append(q) or "Late cancellation is 50 USD.\nSource: appointment-policy › Cancellation policy",
            plan_sources=rules_plan,
            lookup_ticket=TicketLookupTool(session),
            lookup_inventory=InventoryLookupTool(session),
        )
        runner = AgentRunner(deps=deps, state_dir=tmp_path / f"s{len(runners)}", store_text=store_text)
        runners.append(runner)
        return runner

    yield _make
    for runner in runners:
        runner.close()


def test_ticket_question_uses_the_tool_and_not_the_knowledge_base(make_runner) -> None:
    runner = make_runner(FakeApi())
    result = runner.run("What's the status of ticket INC-0042?")

    assert runner.traces.node_sequence(result.run_id) == ["receive_question", "plan_sources", "lookup_ticket", "compose_answer"]
    assert result.sources == ("incident_manager",)
    assert result.outcome == "answered"
    assert result.answer.startswith("Ticket INC-0042 is closed. Category: WORKFORCE. Clinic: us-tx-002 (US).")


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [({"status": 503}, "unavailable"), ({"login_status": 401}, "auth_failed"), ({"not_json": True}, "bad_response")],
)
def test_every_tool_failure_takes_the_fallback_node_with_an_honest_answer(make_runner, overrides, reason) -> None:
    runner = make_runner(FakeApi(**overrides))
    result = runner.run("What's the status of ticket INC-0042?")
    run = runner.traces.get_run(result.run_id)

    assert [s["node"] for s in run["steps"]] == ["receive_question", "plan_sources", "lookup_ticket", "tool_fallback", "compose_answer"]
    assert run["steps"][3]["output"]["fallback"] == {"tool": "ticket_lookup", "reason": reason}
    assert result.outcome == "tool_fallback"
    assert result.answer.startswith("I couldn't confirm ticket INC-0042's status right now")
    assert not any(word in result.answer for word in STATUS_WORDS)


def test_missing_ticket_and_unclear_ticket_are_honest(make_runner) -> None:
    runner = make_runner(FakeApi())
    missing = runner.run("what's the status of ticket 482?")

    assert missing.outcome == "tool_fallback"
    assert missing.answer == (
        "I couldn't find ticket INC-0482 in the incident manager, so I can't confirm its status. Please check the ticket number."
    )


def test_both_sources_run_in_plan_order_and_failure_does_not_stop_the_rag(make_runner) -> None:
    ok = make_runner(FakeApi())
    down = make_runner(FakeApi(status=503))
    question = "Ticket INC-0042: what is its status, and what is our cancellation fee?"

    both = ok.run(question)
    assert rag_questions == ["What is our cancellation fee?"] * 2, "retrieve and generate get only the policy part"
    degraded = down.run(question)

    assert ok.traces.node_sequence(both.run_id) == [
        "receive_question", "plan_sources", "lookup_ticket", "retrieve", "generate_answer", "compose_answer",
    ]
    assert both.sources == ("incident_manager", "knowledge_base")
    assert both.answer.index("Ticket INC-0042 is closed") < both.answer.index(
        "From the HealthCore knowledge base:\nLate cancellation is 50 USD."
    )
    assert down.traces.node_sequence(degraded.run_id) == [
        "receive_question", "plan_sources", "lookup_ticket", "tool_fallback", "retrieve", "generate_answer", "compose_answer",
    ]
    assert degraded.outcome == "tool_fallback" and "50 USD" in degraded.answer


def test_inventory_question_uses_the_inventory_tool_only(make_runner) -> None:
    runner = make_runner(FakeApi())
    result = runner.run("Do we have stock of nitrile exam gloves?")
    missing = runner.run("Do we have stock of MRI contrast agent?")

    assert result.sources == ("inventory_manager",)
    assert result.answer.startswith("Nitrile exam gloves (box of 100) (SKU PPE-GLV-100): 12 in stock, reorder threshold 20 (below threshold).")
    assert missing.outcome == "tool_fallback"
    assert missing.answer.startswith('I couldn\'t find a product matching "MRI contrast agent"')


def test_tool_step_trace_shows_service_method_endpoint_and_latency(make_runner) -> None:
    runner = make_runner(FakeApi())
    result = runner.run("Do we have stock of nitrile exam gloves?")
    call = runner.traces.get_run(result.run_id)["steps"][2]["output"]["tool_call"]

    assert call["tool"] == "inventory_lookup" and call["status"] == "ok"
    assert (call["method"], call["endpoint"], call["http_status"]) == ("GET", "/inventory/products", 200)
    assert call["latency_ms"] >= 0
    assert call["products"] == [{"sku": "PPE-GLV-100", "current_stock": 12, "threshold": 20}]
    assert "input" not in call, "free-text product query is stored only for eval recordings"
