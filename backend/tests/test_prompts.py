"""Prompt loader behaviour."""

from __future__ import annotations

import pytest

from flowagent.prompts import load_prompt, render_prompt


def test_load_system_prompt() -> None:
    text = load_prompt("system")
    assert "FlowAgent" in text
    assert text == text.strip()


def test_load_planner_prompt() -> None:
    text = load_prompt("planner")
    assert "{user_message}" in text


def test_load_missing_prompt_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("does_not_exist")


@pytest.mark.parametrize("bad", ["", "../escape", "foo/bar", "foo\\bar", ".hidden"])
def test_load_prompt_rejects_unsafe_names(bad: str) -> None:
    with pytest.raises(ValueError, match="Invalid prompt name"):
        load_prompt(bad)


def test_render_prompt_substitutes_placeholders() -> None:
    rendered = render_prompt("planner", user_message="book a flight")
    assert "book a flight" in rendered
    assert "{user_message}" not in rendered


def test_render_prompt_missing_placeholder_raises() -> None:
    with pytest.raises(KeyError, match="user_message"):
        render_prompt("planner")


def test_render_prompt_no_placeholders_in_template() -> None:
    # system.md has no placeholders — rendering with extras must be inert.
    rendered = render_prompt("system", ignored="value")
    assert "FlowAgent" in rendered
