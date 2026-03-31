from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pantheon.agent import Agent
from pantheon.internal.memory import Memory
from pantheon.team.pantheon import create_delegation_task_message
from pantheon.utils.token_optimization import (
    PERSISTED_OUTPUT_TAG,
    TIME_BASED_MC_CLEARED_MESSAGE,
    apply_token_optimizations,
    apply_tool_result_budget,
    build_llm_view,
    estimate_total_tokens_from_chars,
    microcompact_messages,
)


def _build_tool_message(tool_call_id: str, content: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "tool_name": "shell",
        "content": content,
    }


def test_apply_tool_result_budget_persists_large_parallel_tool_messages(tmp_path):
    memory = Memory("test-memory")
    messages = [
        {
            "role": "assistant",
            "id": "assistant-1",
            "tool_calls": [
                {"id": "tool-1", "function": {"name": "shell"}},
                {"id": "tool-2", "function": {"name": "shell"}},
                {"id": "tool-3", "function": {"name": "shell"}},
            ],
        },
        _build_tool_message("tool-1", "A" * 90_000),
        _build_tool_message("tool-2", "B" * 90_000),
        _build_tool_message("tool-3", "C" * 90_000),
    ]

    optimized = apply_tool_result_budget(messages, memory=memory, base_dir=tmp_path)

    optimized_tool_messages = [msg for msg in optimized if msg["role"] == "tool"]
    persisted = [
        msg for msg in optimized_tool_messages if msg["content"].startswith(PERSISTED_OUTPUT_TAG)
    ]
    untouched = [
        msg for msg in optimized_tool_messages if not msg["content"].startswith(PERSISTED_OUTPUT_TAG)
    ]

    assert len(persisted) == 1
    assert len(untouched) == 2
    assert "Full output saved to:" in persisted[0]["content"]
    assert "token_optimization" in memory.extra_data

    rerun = apply_tool_result_budget(messages, memory=memory, base_dir=tmp_path)
    assert rerun[1]["content"] == optimized[1]["content"]
    assert rerun[2]["content"] == optimized[2]["content"]
    assert rerun[3]["content"] == optimized[3]["content"]


def test_time_based_microcompact_clears_old_tool_messages():
    old_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
    messages = [
        {"role": "assistant", "id": "assistant-1", "timestamp": old_timestamp},
        _build_tool_message("tool-1", "A" * 20_000),
        _build_tool_message("tool-2", "B" * 20_000),
        _build_tool_message("tool-3", "C" * 20_000),
        _build_tool_message("tool-4", "D" * 20_000),
        _build_tool_message("tool-5", "E" * 20_000),
        _build_tool_message("tool-6", "F" * 20_000),
    ]

    compacted = microcompact_messages(messages, gap_threshold_minutes=60, keep_recent=2)
    compacted_contents = [msg["content"] for msg in compacted if msg["role"] == "tool"]

    assert compacted_contents[:4] == [TIME_BASED_MC_CLEARED_MESSAGE] * 4
    assert compacted_contents[-2:] == ["E" * 20_000, "F" * 20_000]


def test_apply_token_optimizations_reduces_prompt_size(tmp_path):
    memory = Memory("benchmark-memory")
    old_timestamp = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
    messages = [
        {"role": "system", "content": "You are helpful."},
        {
            "role": "assistant",
            "id": "assistant-1",
            "timestamp": old_timestamp,
            "tool_calls": [
                {"id": "tool-1", "function": {"name": "shell"}},
                {"id": "tool-2", "function": {"name": "shell"}},
                {"id": "tool-3", "function": {"name": "shell"}},
                {"id": "tool-4", "function": {"name": "shell"}},
                {"id": "tool-5", "function": {"name": "shell"}},
                {"id": "tool-6", "function": {"name": "shell"}},
            ],
        },
        _build_tool_message("tool-1", "A" * 90_000),
        _build_tool_message("tool-2", "B" * 90_000),
        _build_tool_message("tool-3", "C" * 90_000),
        _build_tool_message("tool-4", "D" * 90_000),
        _build_tool_message("tool-5", "E" * 90_000),
        _build_tool_message("tool-6", "F" * 90_000),
        {"role": "user", "content": "Please summarize the tool outputs."},
    ]

    before_tokens = estimate_total_tokens_from_chars(messages)
    optimized = apply_token_optimizations(
        messages,
        memory=memory,
        base_dir=tmp_path,
    )
    after_tokens = estimate_total_tokens_from_chars(optimized)

    assert after_tokens < before_tokens


def test_build_llm_view_projects_compression_and_preserves_system():
    memory = Memory("projection-memory")
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "first"},
        {"role": "compression", "content": "compressed"},
        {"role": "assistant", "content": "after compression"},
    ]

    view = build_llm_view(messages, memory=memory)

    assert view[0]["role"] == "system"
    assert len(view) == 3
    assert view[1]["role"] == "user"
    assert view[1]["content"] == "compressed"


def test_get_tools_for_llm_is_stably_sorted():
    agent = Agent(name="sorter", instructions="Sort tools")

    def zebra_tool() -> str:
        return "z"

    def alpha_tool() -> str:
        return "a"

    agent.tool(zebra_tool)
    agent.tool(alpha_tool)

    import asyncio

    tools = asyncio.run(agent.get_tools_for_llm())
    tool_names = [tool["function"]["name"] for tool in tools]

    assert tool_names == sorted(tool_names)


def test_create_delegation_task_message_uses_recent_context_and_file_refs(monkeypatch):
    class FakeSummaryGenerator:
        async def generate_summary(self, history, max_tokens=1000):
            return "short summary"

    monkeypatch.setattr(
        "pantheon.chatroom.special_agents.get_summary_generator",
        lambda: FakeSummaryGenerator(),
    )

    history = [
        {"role": "user", "content": "Investigate the failures."},
        {
            "role": "tool",
            "tool_call_id": "tool-1",
            "tool_name": "shell",
            "content": "<persisted-output>\nOutput too large (10KB). Full output saved to: /tmp/tool-1.txt\n\nPreview (first 2KB):\nfoo\n</persisted-output>",
        },
        {"role": "assistant", "content": "I found two likely causes."},
    ]

    import asyncio

    task_message = asyncio.run(
        create_delegation_task_message(
            history,
            "Find the root cause",
            use_summary=True,
        )
    )

    assert "Context Summary:\nshort summary" in task_message
    assert "Recent Context:" in task_message
    assert "Referenced Files:\n- /tmp/tool-1.txt" in task_message
    assert task_message.endswith("Task: Find the root cause")
