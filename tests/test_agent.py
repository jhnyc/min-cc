from types import SimpleNamespace
from typing import Any, Dict

from min_cc.agent import CodingAgent
from min_cc.tools import Tool, ToolRegistry


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("FakeClient ran out of responses")
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class BoomTool(Tool):
    name: str = "boom"
    description: str = "always fails"
    parameters_schema: Dict[str, Any] = {"type": "object", "properties": {}}

    def execute(self, **kwargs) -> str:
        raise ValueError("kaboom")


def assistant_tool_call(name: str, arguments: str, call_id: str = "call_1"):
    tool_call = SimpleNamespace(
        id=call_id, function=SimpleNamespace(name=name, arguments=arguments)
    )
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def assistant_text(content: str):
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def make_agent(fake: FakeClient, registry: ToolRegistry = None) -> CodingAgent:
    agent = CodingAgent(api_key="test-key", registry=registry or ToolRegistry())
    agent.client = fake
    return agent


def test_malformed_tool_arguments_are_returned_to_model():
    fake = FakeClient(
        [assistant_tool_call("bash", "{not json"), assistant_text("recovered")]
    )
    agent = make_agent(fake)

    result = agent.run("do something")

    assert result == "recovered"
    tool_messages = [m for m in agent.state.messages if m.role == "tool"]
    assert "invalid JSON arguments" in tool_messages[0].content


def test_tool_exception_does_not_crash_turn():
    registry = ToolRegistry()
    registry.register_tool(BoomTool())
    fake = FakeClient([assistant_tool_call("boom", "{}"), assistant_text("done")])
    agent = make_agent(fake, registry)

    result = agent.run("trigger the failure")

    assert result == "done"
    tool_messages = [m for m in agent.state.messages if m.role == "tool"]
    assert "Error: tool boom failed" in tool_messages[0].content


def test_max_iterations_forces_final_summary():
    fake = FakeClient(
        [
            assistant_tool_call("bash", '{"command": "ls"}'),
            assistant_tool_call("bash", '{"command": "ls"}'),
            assistant_text("Here is where I got to."),
        ]
    )
    agent = make_agent(fake)

    result = agent.run("loop forever", max_iterations=2)

    assert result == "Here is where I got to."
    tool_calls = [call for call in fake.calls if "tools" in call]
    assert len(tool_calls) == 2
    assert "tools" not in fake.calls[-1]
    assert "Step limit reached" in fake.calls[-1]["messages"][-1]["content"]


def test_llm_error_returns_message_instead_of_raising():
    fake = FakeClient([RuntimeError("connection reset")])
    agent = make_agent(fake)

    result = agent.run("hello")

    assert "Error: LLM request failed" in result
    assert "connection reset" in result
