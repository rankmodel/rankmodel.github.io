# ModelRank Demo — VHS tape script
# Run: vhs demo.tape → generates brand/demo.gif
# Install VHS: brew install charmbracelet/tap/vhs

Output brand/demo.gif

Set Shell "zsh"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Dracula"
Set TypingSpeed 40ms
Set Padding 20

# --- Title Card ---
Type "# ModelRank — The Independent LLM Leaderboard"
Sleep 800ms
Enter
Sleep 400ms

# --- Score a single model ---
Type "python main.py score --model mistralai/Mistral-7B-v0.1"
Sleep 500ms
Enter
Sleep 3000ms

# --- Show leaderboard top 5 ---
Type "python main.py leaderboard --limit 5"
Sleep 500ms
Enter
Sleep 3000ms

# --- Get a badge ---
Type "python scripts/generate_badge.py all meta-llama/Llama-3.1-8B"
Sleep 500ms
Enter
Sleep 2000ms

# --- Compare two models ---
Type "python main.py score --model Qwen/Qwen2.5-7B-Instruct"
Sleep 500ms
Enter
Sleep 2500ms

# --- Final line ---
Type "# Try it: pip install -e . && python main.py leaderboard"
Sleep 800ms
Enter
Sleep 1000ms
