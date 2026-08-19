# ModelRank VS Code Extension

Hover any HuggingFace model id in your editor — `meta-llama/Llama-3.1-8B`,
`Qwen/Qwen3.5-9B`, etc. — and get its **independent ModelRank score**, tier, and
5-dimension breakdown, fetched live from the ModelRank API.

Built on top of the `ModelRankClient` SDK (`api/client.py`); uses only the public
`GET /score/{model_id}` endpoint (no API key required).

## Features

- 🔍 Hover provider that detects `org/model` ids in any language/file.
- 🏆 Shows composite score, tier (S/A/B/C/D), and the 5D breakdown.
- 🔗 Links to the public leaderboard and head-to-head pages.
- ⚙️ Configurable API base URL (`modelrank.baseUrl`); point it at
  `http://localhost:8000` to use a local `python main.py api` server.

## Build & run

```bash
npm install
npm run compile        # emits out/extension.js (requires the VS Code API types)
# Press F5 in VS Code to launch the Extension Development Host and try it.
```

## How it works

`src/extension.ts` registers a `*`-language hover provider. On hover it grabs the
word under the cursor, checks it matches an `org/model` pattern, calls
`{baseUrl}/score/{model_id}`, and renders the result as trusted Markdown.

To contribute a verdict from the editor, call `POST /judge/human` or
`GET /judge/{a}/{b}` on the same client — see `api/client.py`.
