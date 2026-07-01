"""
FIFA World Cup 2026 - Player Performance Dashboard
---------------------------------------------------
An interactive Streamlit app for exploring player and team performance
data from the FIFA World Cup 2026.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import analysis, data_loader

st.set_page_config(
    page_title="FIFA World Cup 2026 - Player Performance",
    page_icon="⚽",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data loading (cached so the CSV is only parsed once per session)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading match data...")
def get_raw_data() -> pd.DataFrame:
    df = data_loader.load_raw_data()
    return data_loader.clean_data(df)


@st.cache_data(show_spinner="Building player summaries...")
def get_summary(raw: pd.DataFrame) -> pd.DataFrame:
    return data_loader.build_player_tournament_summary(raw)


raw_df = get_raw_data()
full_summary = get_summary(raw_df)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.title("⚽ Filters")

teams = sorted(full_summary["team"].unique())
selected_teams = st.sidebar.multiselect("Team(s)", teams, default=[])

positions = sorted(full_summary["position"].unique())
selected_positions = st.sidebar.multiselect("Position(s)", positions, default=[])

stages = sorted(raw_df["tournament_stage"].unique(), key=lambda s: raw_df.loc[raw_df["tournament_stage"] == s, "match_date"].min())
selected_stages = st.sidebar.multiselect("Tournament stage(s)", stages, default=[])

age_min, age_max = int(full_summary["age"].min()), int(full_summary["age"].max())
age_range = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))

min_matches = st.sidebar.slider("Minimum matches played", 1, int(full_summary["matches_played"].max()), 1)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: FIFA World Cup 2026 player performance dataset "
    f"({raw_df.shape[0]:,} match rows, {full_summary.shape[0]:,} players, "
    f"{full_summary['team'].nunique()} teams)."
)

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

filtered_raw = raw_df.copy()
if selected_teams:
    filtered_raw = filtered_raw[filtered_raw["team"].isin(selected_teams)]
if selected_stages:
    filtered_raw = filtered_raw[filtered_raw["tournament_stage"].isin(selected_stages)]

filtered_summary = data_loader.build_player_tournament_summary(filtered_raw) if len(filtered_raw) else full_summary.iloc[0:0]

if selected_positions:
    filtered_summary = filtered_summary[filtered_summary["position"].isin(selected_positions)]
filtered_summary = filtered_summary[
    (filtered_summary["age"] >= age_range[0])
    & (filtered_summary["age"] <= age_range[1])
    & (filtered_summary["matches_played"] >= min_matches)
]

# Keep raw rows in sync with the filtered player set, for charts that need match-level detail.
filtered_raw = filtered_raw[filtered_raw["player_id"].isin(filtered_summary["player_id"])]

# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------

st.title("⚽ FIFA World Cup 2026 — Player Performance Dashboard")
st.caption("Explore player and team performance across the tournament. Use the sidebar to filter by team, position, stage, and age.")

if filtered_summary.empty:
    st.warning("No players match the current filters. Try widening your selection.")
    st.stop()

kpi_cols = st.columns(5)
kpi_cols[0].metric("Players", f"{filtered_summary['player_id'].nunique():,}")
kpi_cols[1].metric("Teams", f"{filtered_summary['team'].nunique():,}")
kpi_cols[2].metric("Total Goals", f"{int(filtered_summary['goals'].sum()):,}")
kpi_cols[3].metric("Total Assists", f"{int(filtered_summary['assists'].sum()):,}")
kpi_cols[4].metric("Avg. Rating", f"{filtered_summary['player_rating'].mean():.2f}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_leaderboards, tab_teams, tab_positions, tab_player, tab_correlations = st.tabs(
    ["🏆 Leaderboards", "🌍 Teams", "📊 Positions & Age", "🔎 Player Explorer", "🔗 Correlations"]
)

# --- Leaderboards -----------------------------------------------------------
with tab_leaderboards:
    top_n = st.slider("Show top N", 5, 25, 10, key="leaderboard_top_n")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Goal Scorers")
        scorers = analysis.top_scorers(filtered_summary, n=top_n)
        fig = px.bar(
            scorers, x="goals", y="player_name", color="team", orientation="h",
            hover_data=["assists", "matches_played"], title=None,
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(scorers, width='stretch', hide_index=True)

    with col2:
        st.subheader("Top Assist Providers")
        assisters = analysis.top_assisters(filtered_summary, n=top_n)
        fig = px.bar(
            assisters, x="assists", y="player_name", color="team", orientation="h",
            hover_data=["goals", "matches_played"],
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(assisters, width='stretch', hide_index=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Top Rated Players")
        min_m = st.slider("Minimum matches for rating leaderboard", 1, 10, 3, key="rating_min_matches")
        rated = analysis.top_rated_players(filtered_summary, n=top_n, min_matches=min_m)
        fig = px.bar(
            rated, x="player_rating", y="player_name", color="team", orientation="h",
            hover_data=["matches_played"],
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(rated, width='stretch', hide_index=True)

    with col4:
        st.subheader("Most Valuable Players")
        valuable = analysis.most_valuable_players(filtered_summary, n=top_n)
        fig = px.bar(
            valuable, x="market_value_eur", y="player_name", color="team", orientation="h",
            hover_data=["club_name"],
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(valuable, width='stretch', hide_index=True)

    st.subheader("🥇 Golden Boot Race")
    race_n = st.slider("Number of players to track", 3, 10, 5, key="race_n")
    race_df = analysis.golden_boot_race(filtered_raw, top_n=race_n)
    if not race_df.empty:
        fig = px.line(
            race_df, x="match_date", y="cumulative_goals", color="player_name",
            markers=True,
        )
        fig.update_layout(height=450, xaxis_title="Match Date", yaxis_title="Cumulative Goals")
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Not enough match data in the current filter to draw the race chart.")

# --- Teams --------------------------------------------------------------
with tab_teams:
    team_stats = analysis.team_summary(filtered_summary)

    st.subheader("Team Comparison")
    max_teams_available = len(team_stats)
    if max_teams_available <= 1:
        n_teams = max_teams_available
        st.caption(f"Only {max_teams_available} team in the current filter — showing it below.")
    else:
        slider_max = min(30, max_teams_available)
        slider_default = min(15, max_teams_available)
        n_teams = st.slider("Number of teams to show", 1, slider_max, slider_default)
    metric = st.selectbox(
        "Metric",
        ["total_goals", "total_assists", "avg_player_rating", "avg_pass_accuracy", "squad_market_value_eur"],
        format_func=lambda c: c.replace("_", " ").title(),
    )
    subset = team_stats.sort_values(metric, ascending=False).head(n_teams)
    fig = px.bar(subset, x=metric, y="team", orientation="h", color=metric, color_continuous_scale="Blues")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500, showlegend=False)
    st.plotly_chart(fig, width='stretch')

    st.subheader("Full Team Table")
    st.dataframe(team_stats, width='stretch', hide_index=True)

# --- Positions & Age ------------------------------------------------------
with tab_positions:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Rating by Position")
        pos_df = analysis.position_breakdown(filtered_summary)
        fig = px.bar(pos_df, x="position", y="avg_rating", color="position", text="player_count")
        fig.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(pos_df, width='stretch', hide_index=True)

    with col2:
        st.subheader("Average Rating by Age Group")
        age_df = analysis.age_vs_performance(filtered_summary)
        fig = px.bar(age_df, x="age_group", y="avg_rating", color="age_group", text="player_count")
        fig.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(age_df, width='stretch', hide_index=True)

# --- Player Explorer --------------------------------------------------------
with tab_player:
    st.subheader("Player Explorer")
    player_names = sorted(filtered_summary["player_name"].unique())
    chosen = st.selectbox("Choose a player", player_names)

    row = filtered_summary[filtered_summary["player_name"] == chosen].iloc[0]

    info_cols = st.columns(4)
    info_cols[0].metric("Team", row["team"])
    info_cols[1].metric("Position", row["position"])
    info_cols[2].metric("Age", int(row["age"]))
    info_cols[3].metric("Matches Played", int(row["matches_played"]))

    stat_cols = st.columns(4)
    stat_cols[0].metric("Goals", int(row["goals"]))
    stat_cols[1].metric("Assists", int(row["assists"]))
    stat_cols[2].metric("Avg. Rating", f"{row['player_rating']:.2f}")
    stat_cols[3].metric("Market Value (€)", f"{int(row['market_value_eur']):,}")

    radar_metrics = [
        "offensive_contribution", "defensive_contribution", "possession_impact",
        "pressure_resistance", "creativity_score", "consistency_score",
    ]
    radar_values = [row[m] for m in radar_metrics]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar_values + [radar_values[0]],
        theta=[m.replace("_", " ").title() for m in radar_metrics] + [radar_metrics[0].replace("_", " ").title()],
        fill="toself",
        name=chosen,
    ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=450, showlegend=False)
    st.plotly_chart(fig, width='stretch')

    st.markdown("##### Match-by-match log")
    player_matches = filtered_raw[filtered_raw["player_name"] == chosen][
        ["match_date", "opponent_team", "tournament_stage", "minutes_played", "goals", "assists", "player_rating"]
    ].sort_values("match_date")
    st.dataframe(player_matches, width='stretch', hide_index=True)

# --- Correlations --------------------------------------------------------
with tab_correlations:
    st.subheader("Correlation Between Key Performance Metrics")
    default_cols = [
        "goals", "assists", "player_rating", "pass_accuracy",
        "distance_covered_km", "market_value_eur", "creativity_score",
    ]
    numeric_cols = filtered_summary.select_dtypes("number").columns.tolist()
    chosen_cols = st.multiselect("Metrics to include", numeric_cols, default=[c for c in default_cols if c in numeric_cols])

    if len(chosen_cols) >= 2:
        corr = analysis.correlation_matrix(filtered_summary, columns=chosen_cols)
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        fig.update_layout(height=550)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Select at least two metrics to see their correlation.")
