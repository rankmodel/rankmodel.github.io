"""LangChain adapter for ModelRank.

Wraps the plain tools from :mod:`integrations.base` into LangChain ``Tool``
objects. ``langchain`` is an optional dependency — this module imports it lazily,
so importing *this* module never fails; only :func:`get_modelrank_langchain_tools`
raises if LangChain is missing.
"""

from typing import List, Optional

from api.client import ModelRankClient

from .base import get_modelrank_tools


def get_modelrank_langchain_tools(client: Optional[ModelRankClient] = None) -> List:
    """Return LangChain ``Tool`` objects for the ModelRank endpoints.

    Requires ``langchain`` (``pip install langchain``). Each tool delegates to the
    same ``run`` method as the plain tools in :mod:`integrations.base`.
    """
    try:
        from langchain.tools import Tool
    except ImportError as e:  # pragma: no cover - exercised only when langchain absent
        raise ImportError(
            "LangChain is not installed. Install it with `pip install langchain` "
            "to use ModelRank LangChain tools."
        ) from e

    tools: List = []
    for t in get_modelrank_tools(client):
        tools.append(
            Tool(name=t.name, func=t.run, description=t.description)
        )
    return tools
