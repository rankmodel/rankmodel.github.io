import * as vscode from 'vscode';

// Matches HuggingFace model ids like meta-llama/Llama-3.1-8B or
// org-name/model.name-1.2 (org and model segments are dot/underscore/dash safe).
const MODEL_ID_RE = /[A-Za-z0-9][\w.\-]*\/[\w.\-]+/g;

interface ModelRankScore {
  model_id?: string;
  composite?: number;
  tier?: string;
  breakdown?: Record<string, number>;
}

const TIER_EMOJI: Record<string, string> = {
  S: '💜',
  A: '💙',
  B: '💚',
  C: '💛',
  D: '❤️',
};

function configBaseUrl(): string {
  const cfg = vscode.workspace.getConfiguration('modelrank');
  const url = cfg.get<string>('baseUrl') || 'https://api.modelrank.com';
  return url.replace(/\/+$/, '');
}

async function fetchScore(modelId: string, baseUrl: string): Promise<ModelRankScore | null> {
  const res = await fetch(`${baseUrl}/score/${encodeURIComponent(modelId)}`);
  if (!res.ok) {
    return null;
  }
  return (await res.json()) as ModelRankScore;
}

function toMarkdown(modelId: string, data: ModelRankScore): vscode.MarkdownString {
  const tier = data.tier ?? '?';
  const composite =
    typeof data.composite === 'number' ? data.composite.toFixed(1) : '?';
  const emoji = TIER_EMOJI[tier] ?? '🏆';

  const md = new vscode.MarkdownString();
  md.appendMarkdown(`**🏆 ModelRank** — \`${modelId}\`\n\n`);
  md.appendMarkdown(`**Score:** ${composite} · **Tier:** ${emoji} ${tier}\n\n`);

  const bd = data.breakdown;
  if (bd) {
    const labels: Record<string, string> = {
      benchmarks: '🧠 Benchmarks',
      efficiency: '⚡ Efficiency',
      community: '🔥 Community',
      recency: '🕐 Recency',
      reproducibility: '✅ Reproducibility',
    };
    const rows = Object.entries(bd)
      .map(([k, v]) => `| ${labels[k] ?? k} | ${typeof v === 'number' ? v.toFixed(1) : v} |`)
      .join('\n');
    md.appendMarkdown(`| Dimension | Score |\n| --- | --- |\n${rows}\n\n`);
  }

  md.appendMarkdown(
    `[Open leaderboard](https://rankmodel.github.io/rankmodel) · ` +
      `[Head-to-head](https://rankmodel.github.io/rankmodel/head-to-head.html)`
  );
  md.isTrusted = true;
  return md;
}

export function activate(context: vscode.ExtensionContext): void {
  const provider = vscode.languages.registerHoverProvider('*', {
    async provideHover(document, position) {
      const range = document.getWordRangeAtPosition(position, MODEL_ID_RE);
      if (!range) {
        return undefined;
      }
      const text = document.getText(range);
      if (!text.includes('/')) {
        return undefined;
      }

      const baseUrl = configBaseUrl();
      try {
        const data = await fetchScore(text, baseUrl);
        if (!data) {
          return undefined;
        }
        return new vscode.Hover(toMarkdown(text, data), range);
      } catch {
        return undefined;
      }
    },
  });

  context.subscriptions.push(provider);
}

export function deactivate(): void {
  // no-op
}
