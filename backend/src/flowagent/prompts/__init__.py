"""Prompt template loader.

Prompts live as Markdown files next to this module so they can be edited
without touching Python code and still ship inside the wheel. They support
``{placeholder}`` interpolation through :func:`render_prompt`.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load a prompt template by name (without the ``.md`` extension).

    >>> load_prompt("system")        # doctest: +SKIP
    'You are FlowAgent...'

    Raises :class:`FileNotFoundError` if the prompt does not exist so that
    typos surface immediately at startup.
    """
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise ValueError(f"Invalid prompt name: {name!r}")

    filename = f"{name}.md"
    package = resources.files(__package__)
    target = package.joinpath(filename)
    if not target.is_file():
        raise FileNotFoundError(
            f"Prompt {name!r} not found at {target}. "
            f"Available: {[p.name for p in package.iterdir() if p.name.endswith('.md')]}"
        )
    return target.read_text(encoding="utf-8").strip()


def render_prompt(name: str, /, **kwargs: object) -> str:
    """Load ``name`` and substitute ``{placeholder}`` markers.

    Uses :py:meth:`str.format_map` so unknown placeholders raise ``KeyError``
    instead of being silently kept as literal text.
    """
    template = load_prompt(name)
    try:
        return template.format_map(kwargs)
    except KeyError as exc:
        raise KeyError(f"Prompt {name!r} requires placeholder {exc.args[0]!r}") from exc


__all__ = ["load_prompt", "render_prompt"]
