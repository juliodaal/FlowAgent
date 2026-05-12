"""FlowAgent — autonomous AI agent with persistent memory and custom tools."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("flowagent")
except PackageNotFoundError:  # pragma: no cover — installed in editable mode pre-build
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
