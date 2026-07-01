# ⚽ FIFA World Cup 2026 — Player Performance Dashboard

An interactive Streamlit dashboard for exploring player and team
performance data from the FIFA World Cup 2026 (54,600 match-level
rows, 1,248 players, 48 teams).

## Features

- **Sidebar filters** — team, position, tournament stage, age range,
  minimum matches played. Every chart and table updates live.
- **Leaderboards tab** — top scorers, top assisters, top-rated players,
  most valuable players, and a "Golden Boot race" showing cumulative
  goals over the tournament.
- **Teams tab** — sortable team comparison chart (goals, assists,
  rating, pass accuracy, squad value) plus a full data table.
- **Positions & Age tab** — average rating by position and by age
  group.
- **Player Explorer tab** — pick any player to see their key stats, a
  radar chart of their attacking/defensive/creative profile, and their
  full match-by-match log.
- **Correlations tab** — an interactive correlation heatmap over any
  combination of performance metrics you choose.

All charts are built with Plotly, so they're zoomable, hoverable, and
exportable straight from the browser.

## Project structure

```
fifa-wc2026-streamlit/
├── .streamlit/
│   └── config.toml         # theme
├── data/
│   └── fifa_world_cup_2026_player_performance.csv
├── src/
│   ├── data_loader.py      # load, clean, aggregate
│   └── analysis.py         # leaderboard / summary functions
├── tests/
│   └── test_analysis.py
├── app.py                  # Streamlit app
├── requirements.txt
├── LICENSE
└── README.md
```

## Setup

```bash
git clone https://github.com/<your-username>/fifa-wc2026-streamlit.git
cd fifa-wc2026-streamlit
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run it

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Deploying

The app is a single `app.py` with no secrets required, so it deploys
as-is to [Streamlit Community Cloud](https://streamlit.io/cloud):
point it at your GitHub repo, set the main file to `app.py`, and
deploy. It also works on Hugging Face Spaces or any host that can run
`streamlit run app.py`.

## Running tests

The underlying data pipeline is covered by a `pytest` suite (11 checks
covering data integrity and leaderboard correctness):

```bash
pytest -v
```

## Dataset

`data/fifa_world_cup_2026_player_performance.csv` — one row per
player per match, with biographical info, match context, and detailed
per-match stats (goals, xG, passing, defensive actions, physical
metrics, and derived rating/impact scores).

## License

MIT — see [LICENSE](LICENSE).
