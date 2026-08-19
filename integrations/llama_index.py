"""LlamaIndex adapter for ModelRank.

Wraps the plain tools from :mod:`integrations.base` into LlamaIndex
``FunctionTool`` objects. ``llama-index`` is an optional dependency — imported
lazily, so importing *this* module never fails.
"""

from typing import List, Optional

from api.client import ModelRankClient

from .base import get_modelrank_tools


def get_modelrank_llama_index_tools(client: Optional[ModelRankClient] = None) -> List:
    """Return LlamaIndex ``FunctionTool`` objects for the ModelRank endpoints.

    Requires ``llama-index`` (``pip install llama-index``). Each tool delegates to
    the same ``run`` method as the plain tools in :mod:`integrations.base`.
    """
    try:
        from llama_index.core.tools import FunctionTool
    except ImportError as e:  # pragma: no cover - exercised only when llama_index absent
        raise ImportError(
            "LlamaIndex is not installed. Install it with `pip install llama-index` "
            "to use ModelRank LlamaIndex tools."
        ) from e

    tools: List = []
    for t in get_modelrank_tools(client):
        tools.append(
            FunctionTool.from_defaults(
                fn=t.run, name=t.name, description=t.description
            )
        )
    return tools
