import re
import sys

with open('scripts/generate_static_assets.py', 'r') as f:
    content = f.read()

# 1. Update navigation links in generate_leaderboard_html
nav_str_old = """          <a href="#" class="text-white">Leaderboard</a>
          <a href="#methodology" class="hover:text-white transition-colors">Methodology</a>
          <a href="pricing.html" class="hover:text-white transition-colors">Pricing</a>"""
nav_str_new = """          <a href="#" class="text-white">Leaderboard</a>
          <a href="methodology.html" class="hover:text-white transition-colors">Methodology</a>
          <a href="quiz.html" class="hover:text-white transition-colors">Quiz</a>
          <a href="collections.html" class="hover:text-white transition-colors">Collections</a>
          <a href="pricing.html" class="hover:text-white transition-colors">Pricing</a>"""
content = content.replace(nav_str_old, nav_str_new)

quiz_fn = '''
def generate_quiz_html() -> str:
    """Generate the interactive recommendation quiz."""
    return """<!DOCTYPE html>
<html lang="en" class="dark" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — Best Model for Your Use Case</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.0/dist/full.css" rel="stylesheet" type="text/css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { base: '#0a0a0f', surface: '#13131a', border: '#232330' },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }
        }
      }
    }
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet"/>
  <style>
    body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
    .step-panel { display: none; opacity: 0; transform: translateX(20px); transition: all 0.4s ease-out; }
    .step-panel.active { display: block; opacity: 1; transform: translateX(0); }
    .card-option { cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
    .card-option:hover { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }
    .card-option.selected { border-color: #3b82f6; background: rgba(59, 130, 246, 0.1); }
  </style>
</head>
<body class="min-h-screen text-gray-200">
  <header class="pt-8 pb-4 border-b border-white/5">
    <div class="container mx-auto px-4 max-w-4xl flex justify-between items-center">
      <a href="index.html" class="text-xl font-black flex items-center gap-2 text-white">🏆 ModelRank</a>
      <div class="text-sm font-medium text-gray-400">
        <a href="index.html" class="hover:text-white mr-4">Leaderboard</a>
        <a href="collections.html" class="hover:text-white">Collections</a>
      </div>
    </div>
  </header>

  <main class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="mb-8">
      <div class="flex justify-between text-xs font-bold text-gray-500 mb-2">
        <span>Step <span id="step-counter">1</span> of 3</span>
      </div>
      <div class="w-full bg-gray-800 rounded-full h-1.5">
        <div id="progress-bar" class="bg-blue-500 h-1.5 rounded-full transition-all duration-300" style="width: 33%"></div>
      </div>
    </div>

    <!-- Step 1 -->
    <div id="step-1" class="step-panel active">
      <h1 class="text-3xl font-black text-white mb-2">What is your primary use case?</h1>
      <p class="text-gray-400 mb-8">Select the task that represents 80%+ of what you'll use the model for.</p>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="use-case-options">
        <div class="glass-card p-6 rounded-2xl card-option" data-value="chat">
          <div class="text-3xl mb-3">💬</div>
          <h3 class="text-lg font-bold text-white mb-1">Chat / Assistant</h3>
          <p class="text-sm text-gray-400">Conversational AI, customer support, general Q&A</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="code">
          <div class="text-3xl mb-3">💻</div>
          <h3 class="text-lg font-bold text-white mb-1">Code Generation</h3>
          <p class="text-sm text-gray-400">Write, explain, debug code — Python, JS, Go</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="rag">
          <div class="text-3xl mb-3">📖</div>
          <h3 class="text-lg font-bold text-white mb-1">RAG / Knowledge Base</h3>
          <p class="text-sm text-gray-400">Retrieve and summarize long documents</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="research">
          <div class="text-3xl mb-3">🔬</div>
          <h3 class="text-lg font-bold text-white mb-1">Research / Reasoning</h3>
          <p class="text-sm text-gray-400">Complex multi-step reasoning, PhD-level questions</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="multilingual">
          <div class="text-3xl mb-3">🌍</div>
          <h3 class="text-lg font-bold text-white mb-1">Multilingual</h3>
          <p class="text-sm text-gray-400">Support for non-English languages</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="edge">
          <div class="text-3xl mb-3">🏎️</div>
          <h3 class="text-lg font-bold text-white mb-1">Edge / On-device</h3>
          <p class="text-sm text-gray-400">Must run on laptop/mobile without cloud</p>
        </div>
      </div>
    </div>

    <!-- Step 2 -->
    <div id="step-2" class="step-panel">
      <button class="text-sm text-gray-400 hover:text-white flex items-center gap-1 mb-4" onclick="goToStep(1)">
        ← Back
      </button>
      <h1 class="text-3xl font-black text-white mb-2">What hardware will you run it on?</h1>
      <p class="text-gray-400 mb-8">This helps us filter out models that won't fit in your memory.</p>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="hardware-options">
        <div class="glass-card p-6 rounded-2xl card-option" data-value="cloud">
          <div class="text-3xl mb-3">☁️</div>
          <h3 class="text-lg font-bold text-white mb-1">Cloud / API</h3>
          <p class="text-sm text-gray-400">Use via API, no local hardware constraints</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="high">
          <div class="text-3xl mb-3">🖥️</div>
          <h3 class="text-lg font-bold text-white mb-1">High-end GPU</h3>
          <p class="text-sm text-gray-400">RTX 4090, A100, 80GB+ VRAM</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="mid">
          <div class="text-3xl mb-3">💻</div>
          <h3 class="text-lg font-bold text-white mb-1">Mid-range GPU</h3>
          <p class="text-sm text-gray-400">RTX 3080/4070, 16-24GB VRAM</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="potato">
          <div class="text-3xl mb-3">🥔</div>
          <h3 class="text-lg font-bold text-white mb-1">Potato</h3>
          <p class="text-sm text-gray-400">CPU only or 8GB RAM — must be tiny</p>
        </div>
      </div>
    </div>

    <!-- Step 3 -->
    <div id="step-3" class="step-panel">
      <button class="text-sm text-gray-400 hover:text-white flex items-center gap-1 mb-4" onclick="goToStep(2)">
        ← Back
      </button>
      <h1 class="text-3xl font-black text-white mb-2">What's your priority?</h1>
      <p class="text-gray-400 mb-8">Trade-off between quality and speed.</p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4" id="priority-options">
        <div class="glass-card p-6 rounded-2xl card-option" data-value="quality">
          <div class="text-3xl mb-3">🏆</div>
          <h3 class="text-lg font-bold text-white mb-1">Best quality</h3>
          <p class="text-sm text-gray-400">Highest possible score, I don't care about speed</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="balanced">
          <div class="text-3xl mb-3">⚡</div>
          <h3 class="text-lg font-bold text-white mb-1">Balanced</h3>
          <p class="text-sm text-gray-400">Good quality + reasonable speed</p>
        </div>
        <div class="glass-card p-6 rounded-2xl card-option" data-value="speed">
          <div class="text-3xl mb-3">🚀</div>
          <h3 class="text-lg font-bold text-white mb-1">Speed first</h3>
          <p class="text-sm text-gray-400">Fastest inference, good enough quality</p>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div id="results" class="step-panel">
      <button class="text-sm text-gray-400 hover:text-white flex items-center gap-1 mb-4" onclick="goToStep(1); resetSelections();">
        ← Start Over
      </button>
      <h1 class="text-3xl font-black text-white mb-2">Top Recommendations</h1>
      <p class="text-gray-400 mb-8">Based on your selections: <span id="summary-text" class="text-blue-400 font-bold"></span></p>
      
      <div id="loading" class="text-center py-12">
        <span class="loading loading-spinner loading-lg text-primary"></span>
        <p class="mt-4 text-gray-400">Analyzing models...</p>
      </div>

      <div id="recommendations-container" class="space-y-4 hidden"></div>

      <div class="mt-8 flex gap-4 hidden" id="action-buttons">
        <a href="index.html" class="btn btn-outline">Compare all models</a>
        <button onclick="shareResults()" class="btn btn-primary">Share Results</button>
      </div>
    </div>
  </main>

  <script>
    let selections = { useCase: '', hardware: '', priority: '' };
    const LEADERBOARD_URL = 'leaderboard.json';
    let leaderboardData = null;

    function resetSelections() {
      selections = { useCase: '', hardware: '', priority: '' };
      document.querySelectorAll('.card-option').forEach(el => el.classList.remove('selected'));
    }

    function goToStep(step) {
      document.querySelectorAll('.step-panel').forEach(el => el.classList.remove('active'));
      document.getElementById(`step-${step}`)?.classList.add('active');
      document.getElementById('step-counter').innerText = step;
      document.getElementById('progress-bar').style.width = `${(step/3)*100}%`;
    }

    function handleSelection(step, key, value, el) {
      selections[key] = value;
      const parent = el.closest('.grid');
      parent.querySelectorAll('.card-option').forEach(card => card.classList.remove('selected'));
      el.classList.add('selected');
      
      setTimeout(() => {
        if (step < 3) {
          goToStep(step + 1);
        } else {
          showResults();
        }
      }, 300);
    }

    document.getElementById('use-case-options').addEventListener('click', e => {
      const card = e.target.closest('.card-option');
      if(card) handleSelection(1, 'useCase', card.dataset.value, card);
    });
    document.getElementById('hardware-options').addEventListener('click', e => {
      const card = e.target.closest('.card-option');
      if(card) handleSelection(2, 'hardware', card.dataset.value, card);
    });
    document.getElementById('priority-options').addEventListener('click', e => {
      const card = e.target.closest('.card-option');
      if(card) handleSelection(3, 'priority', card.dataset.value, card);
    });

    function calcFit(model, useCase, hardware, priority) {
      let score = model.composite;
      const b = model.breakdown || {};
      
      // Use case adjustments
      if (useCase === 'code') score += (b.benchmarks || 0) * 0.3;
      if (useCase === 'edge') score += (b.efficiency || 0) * 0.5 - (model.composite * 0.2);
      if (useCase === 'multilingual') score += (b.community || 0) * 0.2;
      if (useCase === 'research') score += (b.benchmarks || 0) * 0.4;
      
      // Hardware filter
      const eff = b.efficiency || 0;
      if (hardware === 'potato') { if (eff < 70) score -= 40; else score += 20; }
      if (hardware === 'mid') { if (eff < 40) score -= 20; }
      
      // Priority
      if (priority === 'speed') score += (b.efficiency || 0) * 0.3;
      if (priority === 'quality') score += (b.benchmarks || 0) * 0.2;
      
      return score;
    }

    async function fetchLeaderboard() {
      if (leaderboardData) return leaderboardData;
      try {
        const res = await fetch(LEADERBOARD_URL);
        leaderboardData = await res.json();
        return leaderboardData;
      } catch (err) {
        console.error(err);
        return { models: [] };
      }
    }

    async function showResults() {
      document.querySelectorAll('.step-panel').forEach(el => el.classList.remove('active'));
      document.getElementById('results').classList.add('active');
      document.getElementById('progress-bar').style.width = '100%';
      
      const labels = {
        chat: 'Chat', code: 'Code', rag: 'RAG', research: 'Research', multilingual: 'Multilingual', edge: 'Edge',
        cloud: 'Cloud', high: 'High-end GPU', mid: 'Mid-range GPU', potato: 'Potato PC',
        quality: 'Quality', balanced: 'Balanced', speed: 'Speed'
      };
      document.getElementById('summary-text').innerText = `${labels[selections.useCase]} on ${labels[selections.hardware]} (${labels[selections.priority]})`;
      
      const data = await fetchLeaderboard();
      document.getElementById('loading').classList.add('hidden');
      
      const scored = data.models.map(m => ({
        ...m,
        fit: calcFit(m, selections.useCase, selections.hardware, selections.priority)
      })).sort((a, b) => b.fit - a.fit).slice(0, 3);
      
      const container = document.getElementById('recommendations-container');
      container.innerHTML = '';
      container.classList.remove('hidden');
      document.getElementById('action-buttons').classList.remove('hidden');

      scored.forEach((m, idx) => {
        const parts = m.model_id.split('/');
        const name = parts.length > 1 ? parts[1] : m.model_id;
        const org = parts.length > 1 ? parts[0] : '';
        const html = `
          <div class="glass-card p-6 rounded-2xl flex flex-col md:flex-row gap-6 items-center border-l-4 ${idx===0 ? 'border-l-blue-500' : 'border-l-gray-600'}">
            <div class="text-4xl font-black text-gray-500">#${idx+1}</div>
            <div class="flex-1">
              <div class="text-xs text-gray-500">${org}</div>
              <h3 class="text-xl font-bold text-white"><a href="https://huggingface.co/${m.model_id}" target="_blank" class="hover:underline">${name}</a></h3>
              <p class="text-sm text-gray-400 mt-1">Score: <span class="text-blue-400 font-bold">${m.composite.toFixed(1)}</span> • Tier: <span class="badge badge-sm badge-outline">${m.tier}</span> • Efficiency: ${m.breakdown?.efficiency?.toFixed(1)||'N/A'}</p>
              <p class="text-sm text-gray-300 mt-2 bg-white/5 p-2 rounded italic">"Best fit due to high ${selections.priority==='speed'||selections.hardware==='potato'?'efficiency':'benchmark performance'} for this hardware."</p>
            </div>
            <div>
              <img src="${m.badge_url}" alt="Score Badge" class="h-8">
            </div>
          </div>
        `;
        container.innerHTML += html;
      });
      
      window.shareText = `ModelRank recommends ${scored[0]?.model_id || 'these models'} for ${labels[selections.useCase]} on ${labels[selections.hardware]}. Check it out at ModelRank!`;
    }
    
    function shareResults() {
      const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(window.shareText)}`;
      window.open(url, '_blank');
    }
  </script>
</body>
</html>"""
'''

collections_fn = '''
def generate_collections_html() -> str:
    """Generate the curated collections page."""
    return """<!DOCTYPE html>
<html lang="en" class="dark" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank — Model Collections</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.0/dist/full.css" rel="stylesheet" type="text/css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { base: '#0a0a0f', surface: '#13131a', border: '#232330' },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }
        }
      }
    }
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet"/>
  <style>
    body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
    details > summary { list-style: none; }
    details > summary::-webkit-details-marker { display: none; }
  </style>
</head>
<body class="min-h-screen text-gray-200">
  <header class="pt-16 pb-12 border-b border-white/5 relative overflow-hidden">
    <div class="absolute top-0 right-0 w-[400px] h-[400px] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>
    <div class="container mx-auto px-4 max-w-6xl relative z-10">
      <nav class="flex items-center justify-between mb-12">
        <a href="index.html" class="text-2xl font-black tracking-tight flex items-center gap-2 text-white">🏆 ModelRank</a>
        <div class="flex items-center gap-6 text-sm font-medium text-gray-400">
          <a href="index.html" class="hover:text-white">Leaderboard</a>
          <a href="quiz.html" class="hover:text-white">Quiz</a>
        </div>
      </nav>
      <h1 class="text-4xl md:text-5xl font-black text-white mb-4">Model Collections</h1>
      <p class="text-xl text-gray-400">Curated lists of top performers by category</p>
      <p class="text-sm text-gray-500 mt-2" id="last-updated">Last updated: fetching...</p>
    </div>
  </header>

  <main class="container mx-auto px-4 py-12 max-w-6xl">
    <div class="grid grid-cols-1 gap-6" id="collections-container">
      <div class="text-center py-12"><span class="loading loading-spinner loading-lg text-primary"></span></div>
    </div>
  </main>

  <script>
    async function loadCollections() {
      try {
        const res = await fetch('leaderboard.json');
        const data = await res.json();
        document.getElementById('last-updated').innerText = 'Last updated: ' + (data.updated_at || new Date().toISOString());
        
        const models = data.models || [];
        
        const collections = [
          {
            id: 'top-overall',
            title: '🏆 Top Overall',
            desc: 'Top 10 models by composite score',
            models: [...models].sort((a,b) => b.composite - a.composite).slice(0, 10)
          },
          {
            id: 'efficiency',
            title: '⚡ Efficiency Champions',
            desc: 'Top 10 by efficiency score (best for edge/CPU)',
            models: [...models].sort((a,b) => (b.breakdown?.efficiency||0) - (a.breakdown?.efficiency||0)).slice(0, 10)
          },
          {
            id: 'code',
            title: '💻 Best for Code',
            desc: 'Models excelling in coding benchmarks (simulated)',
            models: [...models].filter(m => m.model_id.toLowerCase().includes('coder') || m.model_id.toLowerCase().includes('code') || m.composite > 75).slice(0, 10)
          },
          {
            id: 'trending',
            title: '🔥 Trending Right Now',
            desc: 'Top 10 by community score',
            models: [...models].sort((a,b) => (b.breakdown?.community||0) - (a.breakdown?.community||0)).slice(0, 10)
          },
          {
            id: 'fresh',
            title: '🆕 Freshest Models',
            desc: 'Top 10 by recency score',
            models: [...models].sort((a,b) => (b.breakdown?.recency||0) - (a.breakdown?.recency||0)).slice(0, 10)
          },
          {
            id: 'sa-tier',
            title: '💜 S & A Tier Only',
            desc: 'Elite models scoring 80+',
            models: [...models].filter(m => m.tier === 'S' || m.tier === 'A').sort((a,b) => b.composite - a.composite)
          }
        ];

        const container = document.getElementById('collections-container');
        container.innerHTML = '';
        
        collections.forEach(col => {
          let rowsHtml = '';
          col.models.forEach(m => {
            const parts = m.model_id.split('/');
            const name = parts.length > 1 ? parts[1] : m.model_id;
            rowsHtml += `
              <div class="flex items-center justify-between p-3 border-b border-white/5 hover:bg-white/5">
                <div class="flex items-center gap-3">
                  <span class="text-gray-500 font-mono text-sm">#${m.rank}</span>
                  <a href="https://huggingface.co/${m.model_id}" class="text-white font-bold hover:underline">${name}</a>
                </div>
                <div class="flex items-center gap-4">
                  <span class="text-blue-400 font-mono font-bold">${m.composite.toFixed(1)}</span>
                  <span class="badge badge-sm badge-outline">${m.tier}</span>
                  <button onclick="navigator.clipboard.writeText('![ModelRank](${m.badge_url})')" class="btn btn-xs btn-ghost text-gray-400">Copy Badge</button>
                </div>
              </div>
            `;
          });

          const html = `
            <details class="glass-card rounded-2xl group" ${col.id === 'top-overall' ? 'open' : ''}>
              <summary class="p-6 cursor-pointer flex justify-between items-center">
                <div>
                  <h2 class="text-2xl font-black text-white">${col.title}</h2>
                  <p class="text-gray-400 text-sm mt-1">${col.desc} — ${col.models.length} models</p>
                </div>
                <div class="text-gray-500 transition-transform group-open:rotate-180">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                </div>
              </summary>
              <div class="px-6 pb-6 pt-2 border-t border-white/5">
                ${rowsHtml}
              </div>
            </details>
          `;
          container.innerHTML += html;
        });

      } catch (err) {
        document.getElementById('collections-container').innerHTML = '<p class="text-red-500">Failed to load collections.</p>';
      }
    }
    loadCollections();
  </script>
</body>
</html>"""
'''

methodology_fn = '''
def generate_methodology_html() -> str:
    """Generate the methodology page."""
    return """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ModelRank Scoring Methodology — How We Evaluate Open-Weight AI Models</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@3.9.0/dist/full.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: { base: '#0a0a0f', surface: '#13131a', border: '#232330' },
          fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] }
        }
      }
    }
  </script>
  <style>body { background-color: #0a0a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; } .glass-card { background: rgba(19, 19, 26, 0.7); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }</style>
</head>
<body class="min-h-screen text-gray-200">
  <div class="container mx-auto px-4 py-12 max-w-4xl">
    <div class="mb-8"><a href="index.html" class="btn btn-outline btn-sm border-white/20 text-gray-300 hover:bg-white/10 hover:border-white/30">← Back to Leaderboard</a></div>
    <h1 class="text-4xl md:text-5xl font-black mb-6 tracking-tight text-white">ModelRank Scoring Methodology</h1>
    <p class="text-xl text-gray-400 mb-12">Built for developers, not marketing teams. Every score is reproducible, open-source, and conflict-of-interest-free.</p>
    
    <div class="space-y-12">
      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">1. The Five Dimensions</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="glass-card p-6 rounded-2xl border-t-4 border-blue-500">
            <h3 class="font-bold text-xl mb-1 text-white">Benchmarks (40%)</h3>
            <p class="text-sm text-gray-400 mb-2">Evaluates logical reasoning, coding, math, and knowledge.</p>
            <p class="text-xs text-gray-500">Sources: HuggingFace Evals, Open LLM Leaderboard V2. A 90/100 means top-tier reasoning. Limitation: Does not capture creative writing preference.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-green-500">
            <h3 class="font-bold text-xl mb-1 text-white">Efficiency (20%)</h3>
            <p class="text-sm text-gray-400 mb-2">Throughput, VRAM usage, and parameter-to-performance ratio.</p>
            <p class="text-xs text-gray-500">Sources: Context length metadata, param count. A 90/100 means runs fast on consumer GPUs. Limitation: Static estimates, not real-time profiling.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-purple-500">
            <h3 class="font-bold text-xl mb-1 text-white">Community (20%)</h3>
            <p class="text-sm text-gray-400 mb-2">Usage, momentum, and mindshare.</p>
            <p class="text-xs text-gray-500">Sources: HF Downloads, likes. A 90/100 means mass adoption. Limitation: Can be skewed by early hype or bots.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-yellow-500">
            <h3 class="font-bold text-xl mb-1 text-white">Freshness (10%)</h3>
            <p class="text-sm text-gray-400 mb-2">Time since release and update frequency.</p>
            <p class="text-xs text-gray-500">Sources: Last modified dates. A 90/100 means updated this week. Limitation: Penalizes stable, completed models over time.</p>
          </div>
          <div class="glass-card p-6 rounded-2xl border-t-4 border-red-500">
            <h3 class="font-bold text-xl mb-1 text-white">Reproducibility (10%)</h3>
            <p class="text-sm text-gray-400 mb-2">Open weights, clear license, verified origin.</p>
            <p class="text-xs text-gray-500">Sources: Hub metadata, safetensors presence. A 90/100 means fully open (MIT/Apache) and safe.</p>
          </div>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">2. Benchmark Coverage Table</h2>
        <div class="glass-card rounded-2xl overflow-hidden">
          <table class="table w-full">
            <thead class="bg-white/5 text-gray-300">
              <tr><th>Benchmark</th><th>Domain</th><th>Source</th><th>Weight</th><th>Notes</th></tr>
            </thead>
            <tbody class="text-sm text-gray-400">
              <tr class="border-b border-white/5"><td>MMLU-Pro</td><td>General knowledge</td><td>HuggingFace Evals</td><td>20%</td><td>...</td></tr>
              <tr class="border-b border-white/5"><td>GPQA Diamond</td><td>PhD-level reasoning</td><td>idavidrein/gpqa</td><td>20%</td><td>...</td></tr>
              <tr class="border-b border-white/5"><td>HLE</td><td>Expert-level</td><td>...</td><td>15%</td><td>Humanity's Last Exam</td></tr>
              <tr class="border-b border-white/5"><td>GSM8K</td><td>Math word problems</td><td>...</td><td>10%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>HumanEval</td><td>Code generation</td><td>openai/...</td><td>10%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>BBH</td><td>Big-Bench Hard</td><td>...</td><td>8%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>IFEval</td><td>Instruction following</td><td>...</td><td>7%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>MuSR</td><td>Multi-step reasoning</td><td>...</td><td>5%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>MATH</td><td>Advanced math</td><td>...</td><td>5%</td><td></td></tr>
              <tr class="border-b border-white/5"><td>ARC-Challenge</td><td>Science reasoning</td><td>...</td><td>fallback</td><td></td></tr>
              <tr class="border-b border-white/5"><td>HellaSwag</td><td>Commonsense NLI</td><td>...</td><td>fallback</td><td></td></tr>
              <tr class="border-b border-white/5"><td>TruthfulQA</td><td>Factual accuracy</td><td>...</td><td>fallback</td><td></td></tr>
              <tr><td>WinoGrande</td><td>Winograd schema</td><td>...</td><td>fallback</td><td></td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">3. Normalization & Confidence</h2>
        <p class="text-gray-400">Raw benchmark values from HF are 0.0-1.0, we multiply by 100. Frontier benchmarks (MMLU-Pro, GPQA etc.) take priority. When only classic benchmarks found: 0.85x confidence penalty, capped at 75/100. Coverage confidence: high/medium/low based on how many benchmarks found.</p>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">4. Tier System</h2>
        <div class="glass-card rounded-2xl overflow-hidden">
          <table class="table w-full">
            <thead class="bg-white/5 text-gray-300">
              <tr><th>Tier</th><th>Score Range</th><th>Current Examples</th></tr>
            </thead>
            <tbody class="text-sm text-gray-400">
              <tr class="border-b border-white/5"><td><span class="text-purple-400 font-bold">S</span></td><td>90-100</td><td>(none yet — GPT-4 class)</td></tr>
              <tr class="border-b border-white/5"><td><span class="text-blue-400 font-bold">A</span></td><td>80-89</td><td>gemma-4-31B-it (82.97), Qwen3.5-9B (81.52)</td></tr>
              <tr class="border-b border-white/5"><td><span class="text-green-400 font-bold">B</span></td><td>70-79</td><td>DeepSeek-R1 (78.3), phi-4 (72.89)</td></tr>
              <tr class="border-b border-white/5"><td><span class="text-yellow-400 font-bold">C</span></td><td>60-69</td><td>gpt-oss-20b (69.81)</td></tr>
              <tr><td><span class="text-red-400 font-bold">D</span></td><td>&lt;60</td><td>Legacy models</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">5. ELO Comparison Formula</h2>
        <div class="glass-card p-6 rounded-2xl mb-4">
          <p class="font-mono text-blue-400 text-center text-lg">P(A beats B) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))</p>
        </div>
        <p class="text-gray-400">Example: Qwen3.5-9B (81.52) vs DeepSeek-R1 (78.3)<br>
        • ELO_A = 800 + 81.52*8 = 1452, ELO_B = 800 + 78.3*8 = 1426<br>
        • P(Qwen beats DeepSeek) = 1 / (1 + 10^((1426 - 1452) / 400)) = 0.537 = 53.7% win probability</p>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">6. Extended Metadata (10 signals)</h2>
        <p class="text-gray-400">context_window, vram_tier, license_score, finetune_friendly, multilingual, safety_score, update_velocity, inference_coverage, community_momentum, hub_completeness.</p>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">7. What We Don't Measure (Honest Limitations)</h2>
        <ul class="list-disc pl-5 text-gray-400 space-y-2">
          <li>Human preference (requires live inference infrastructure)</li>
          <li>API latency and cost per token</li>
          <li>Alignment and safety (beyond TruthfulQA)</li>
          <li>Benchmark contamination (we can't verify if models saw test data)</li>
          <li>Dialect/regional language performance</li>
        </ul>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-6 text-white">8. Changelog</h2>
        <div class="glass-card rounded-2xl overflow-hidden">
          <table class="table w-full">
            <thead class="bg-white/5 text-gray-300">
              <tr><th>Version</th><th>Date</th><th>Changes</th></tr>
            </thead>
            <tbody class="text-sm text-gray-400">
              <tr class="border-b border-white/5"><td>2.0.0</td><td>2026-08-13</td><td>10 extended metadata signals, Shields.io endpoint, pricing page</td></tr>
              <tr class="border-b border-white/5"><td>1.1.0</td><td>2026-08-13</td><td>GitHub Pages CDN, 71 models, HuggingFace Space</td></tr>
              <tr><td>1.0.0</td><td>2026-08-13</td><td>Initial: 5D scoring, ELO, SVG badges, 27 tests</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 class="text-3xl font-bold mb-4 text-white">9. Cite ModelRank</h2>
        <div class="mockup-code bg-base-300 text-sm">
          <pre><code>@software{modelrank2026,
  author = {ModelRank Team},
  title = {ModelRank: Composite Scoring and Embeddable Badges for Open-Weight AI Models},
  year = {2026},
  url = {https://github.com/rankmodel/rankmodel},
  license = {MIT}
}</code></pre>
        </div>
      </section>
    </div>
  </div>
</body>
</html>"""
'''

content = re.sub(
    r'def generate_methodology_html\(\) -> str:\n.*?return """.*?</html>"""\n',
    methodology_fn,
    content,
    flags=re.DOTALL
)

# Insert the two new functions before generate_pricing_html
content = content.replace('def generate_pricing_html() -> str:', f"{quiz_fn}\n{collections_fn}\ndef generate_pricing_html() -> str:")

# Insert main calls
main_replace_old = """    # Trust Building Pages
    (OUTPUT_DIR / 'methodology.html').write_text(generate_methodology_html(), encoding='utf-8')
    logger.info('   methodology.html trust page')
    (OUTPUT_DIR / 'api.html').write_text(generate_api_html(), encoding='utf-8')"""

main_replace_new = """    # Trust Building Pages
    (OUTPUT_DIR / 'methodology.html').write_text(generate_methodology_html(), encoding='utf-8')
    logger.info('   methodology.html — FULL VERSION')
    (OUTPUT_DIR / 'quiz.html').write_text(generate_quiz_html(), encoding='utf-8')
    logger.info('   quiz.html — model recommendation quiz')
    (OUTPUT_DIR / 'collections.html').write_text(generate_collections_html(), encoding='utf-8')
    logger.info('   collections.html — curated collections')
    (OUTPUT_DIR / 'api.html').write_text(generate_api_html(), encoding='utf-8')"""

content = content.replace(main_replace_old, main_replace_new)

with open('scripts/generate_static_assets.py', 'w') as f:
    f.write(content)
