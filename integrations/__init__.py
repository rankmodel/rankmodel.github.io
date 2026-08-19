"""ModelRank integrations.

Thin, dependency-optional wrappers around :class:`api.client.ModelRankClient`
so ModelRank can be dropped into agent frameworks:

- :mod:`integrations.base` — plain Python tools (always available, fully tested).
- :func:`integrations.langchain.get_modelrank_langchain_tools` — LangChain
  ``Tool`` objects (requires ``langchain``).
- :func:`integrations.llama_index.get_modelrank_llama_index_tools` — LlamaIndex
  ``FunctionTool`` objects (requires ``llama-index``).

The plain tools in :mod:`integrations.base` are the single source of truth; the
framework adapters just wrap them.
"""
