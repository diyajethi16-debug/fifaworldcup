# World Cup 2026 — Player Stats Dashboard

## Run locally
1. Install dependencies:
   pip install -r requirements.txt
2. Launch the app (make sure data.csv is in the same folder as app.py):
   streamlit run app.py
3. Your browser opens at http://localhost:8501

## Dataset
`data.csv` is a season/tournament aggregate stats file — one row per player
(1,248 players across 48 national teams), with fields like goals, assists,
shots, cards, per-90 rates, and dedicated goalkeeper stats (saves, save %,
clean sheets). Age is stored as "years-days" and parsed automatically.

## What's inside
- **Overview** — top-scoring teams, squad composition by position, age
  distribution, minutes vs goal contribution scatter, card discipline by team
- **Player Explorer** — search any player, see a profile card + per-90 output
  chart + full sortable player table
- **Team Comparison** — compare 2+ teams on goals, assists, shots, tackles,
  interceptions, average age, and cards
- **Leaderboards** — top 15 players by any stat you pick (goals, assists,
  tackles won, interceptions, crosses, per-90 rates, etc.)
- **Goalkeepers & Radar** — dedicated GK leaderboards (save %, clean sheets)
  plus a percentile-normalized radar chart to compare up to 4 outfield players

Sidebar filters (team, position, age, minutes, starter status, name search)
apply across all tabs.
