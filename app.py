import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="World Cup 2026 — Player Stats Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# STYLING
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: radial-gradient(circle at 10% 0%, #0f1b3d 0%, #0a1128 45%, #060a1a 100%);
    color: #f4f6fb;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1a3e 0%, #0a1230 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
h1, h2, h3, h4 { color: #ffffff !important; font-weight: 800 !important; }
.hero {
    padding: 1.6rem 2rem; border-radius: 18px;
    background: linear-gradient(120deg, #12224f 0%, #1a2f6b 45%, #2a3f8f 100%);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1.4rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.hero h1 { font-size: 2.1rem; margin: 0; letter-spacing: -0.5px; }
.hero p { color: #b9c4e6; margin: 0.3rem 0 0 0; font-size: 1.02rem; }
.kpi-card {
    background: linear-gradient(145deg, #101c42 0%, #16234f 100%);
    border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
    padding: 1.1rem 1.3rem; box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    transition: transform 0.15s ease;
}
.kpi-card:hover { transform: translateY(-3px); border-color: rgba(255,215,0,0.35); }
.kpi-label { color: #93a1c9; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.kpi-value { color: #ffffff; font-size: 1.35rem; font-weight: 800; margin-top: 0.15rem; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background: #101c42; border-radius: 10px 10px 0 0; color: #b9c4e6;
    font-weight: 600; padding: 10px 18px; border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(120deg,#2a3f8f,#3d5bd9) !important; color: white !important;
}
.player-card {
    background: linear-gradient(145deg, #101c42 0%, #182a5c 100%);
    border: 1px solid rgba(255,215,0,0.25); border-radius: 16px;
    padding: 1.2rem 1.4rem; box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}
hr { border-color: rgba(255,255,255,0.08); }
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #0a1128; }
::-webkit-scrollbar-thumb { background: #2a3f8f; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# DATA LOADING & CLEANING
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")

    # age is stored as "YY-DDD" (years-days) -> convert to a clean float
    def parse_age(a):
        if pd.isna(a):
            return np.nan
        s = str(a)
        if "-" in s:
            y, d = s.split("-")
            try:
                return round(int(y) + int(d) / 365, 1)
            except ValueError:
                return np.nan
        try:
            return float(s)
        except ValueError:
            return np.nan

    df["age_years"] = df["age"].apply(parse_age)

    # primary position = first listed position (players can have multiple, e.g. "FW,MF")
    df["position_primary"] = df["position"].fillna("Unknown").apply(lambda x: x.split(",")[0])
    df["is_goalkeeper"] = df["position_primary"] == "GK"

    # fill numeric NaNs with 0 for aggregate-friendly stats (outfield metrics only)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    fill_zero_cols = [c for c in numeric_cols if not c.startswith("gk_") and c not in
                       ["shots_on_target_pct", "goals_per_shot", "goals_per_shot_on_target",
                        "minutes_per_start", "minutes_per_sub", "plus_minus_wowy", "points_per_game", "minutes_pct"]]
    df[fill_zero_cols] = df[fill_zero_cols].fillna(0)

    df["club"] = df["club"].fillna("Unattached / Not listed")

    # a few players share the same name across different teams (e.g. two
    # different "Emiliano Martínez") -> build an unambiguous display label
    dupe_names = df["player"][df["player"].duplicated(keep=False)].unique()
    df["player_label"] = np.where(
        df["player"].isin(dupe_names),
        df["player"] + " (" + df["team"] + ")",
        df["player"]
    )
    return df

df = load_data()

# ----------------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------------
st.sidebar.markdown("## ⚽ Filters")
st.sidebar.markdown("Refine the player pool across the sidebar filters below.")

teams = st.sidebar.multiselect("Team (Nation)", sorted(df["team"].unique()))
positions = st.sidebar.multiselect("Position", sorted(df["position_primary"].unique()))

age_min = int(np.floor(df["age_years"].min(skipna=True)))
age_max = int(np.ceil(df["age_years"].max(skipna=True)))
age_range = st.sidebar.slider("Age Range", age_min, age_max, (age_min, age_max))

min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, int(df["minutes"].max()), 0, step=10)
only_starters = st.sidebar.checkbox("Only players with at least 1 start", value=False)

search_name = st.sidebar.text_input("🔍 Search Player Name")

st.sidebar.markdown("---")
st.sidebar.caption(f"Dataset: {df['player'].nunique():,} players · {df['team'].nunique()} teams · {df['club'].nunique()} clubs")

fdf = df.copy()
if teams:
    fdf = fdf[fdf["team"].isin(teams)]
if positions:
    fdf = fdf[fdf["position_primary"].isin(positions)]
fdf = fdf[(fdf["age_years"] >= age_range[0]) & (fdf["age_years"] <= age_range[1]) | fdf["age_years"].isna()]
fdf = fdf[fdf["minutes"].fillna(0) >= min_minutes]
if only_starters:
    fdf = fdf[fdf["games_starts"] > 0]
if search_name:
    fdf = fdf[fdf["player"].str.contains(search_name, case=False, na=False)]

if fdf.empty:
    st.warning("No players match your filters. Try widening your selection.")
    st.stop()

# ----------------------------------------------------------------------------
# HERO HEADER
# ----------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>🏆 World Cup 2026 — Player Stats Dashboard</h1>
    <p>Explore goals, assists, discipline, and advanced per-90 metrics for every player and team in the tournament.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------------
total_goals = int(fdf["goals"].sum())
total_assists = int(fdf["assists"].sum())
avg_age = fdf["age_years"].mean()
top_scorer = fdf.loc[fdf["goals"].idxmax()]
n_players = fdf["player"].nunique()
n_teams = fdf["team"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)
kpis = [
    (k1, "⚽ Total Goals", f"{total_goals:,}"),
    (k2, "🎯 Total Assists", f"{total_assists:,}"),
    (k3, "🎂 Avg Age", f"{avg_age:.1f} yrs"),
    (k4, "👑 Top Scorer", f"{top_scorer['goals']:.0f} — {top_scorer['player']}"),
    (k5, "🌍 Players / Teams", f"{n_players:,} / {n_teams}"),
]
for col, label, value in kpis:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", "🧑‍💼 Player Explorer", "🌍 Team Comparison",
    "🥇 Leaderboards", "🧤 Goalkeepers & Radar"
])

COLOR_SEQ = px.colors.qualitative.Vivid
TEMPLATE = "plotly_dark"

def style_fig(fig, height=420):
    fig.update_layout(
        template=TEMPLATE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#f4f6fb"), height=height,
        margin=dict(l=10, r=10, t=50, b=10), legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig

# ---------------- TAB 1: OVERVIEW ----------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        top_teams_goals = fdf.groupby("team")["goals"].sum().sort_values(ascending=False).head(12)
        fig = px.bar(top_teams_goals, x=top_teams_goals.values, y=top_teams_goals.index, orientation="h",
                     title="Top 12 Teams by Total Goals", labels={"x": "Goals", "y": ""},
                     color=top_teams_goals.values, color_continuous_scale="Sunsetdark")
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with c2:
        pos_dist = fdf["position_primary"].value_counts()
        fig = px.pie(pos_dist, values=pos_dist.values, names=pos_dist.index, hole=0.5,
                     title="Squad Composition by Position", color_discrete_sequence=COLOR_SEQ)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = px.histogram(fdf, x="age_years", nbins=20, title="Age Distribution",
                            color_discrete_sequence=["#4fd1c5"])
        fig.update_layout(bargap=0.05)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with c4:
        scat = fdf[fdf["minutes"] > 0]
        fig = px.scatter(scat, x="minutes", y="goals_assists", color="position_primary",
                          hover_name="player", hover_data=["team", "club"],
                          title="Minutes Played vs Goal Contributions",
                          color_discrete_sequence=COLOR_SEQ)
        st.plotly_chart(style_fig(fig), use_container_width=True)

    st.markdown("#### 🟨🟥 Discipline: Cards by Team")
    cards_team = fdf.groupby("team")[["cards_yellow", "cards_red"]].sum().sort_values("cards_yellow", ascending=False).head(15)
    fig = px.bar(cards_team, x=cards_team.index, y=["cards_yellow", "cards_red"], barmode="group",
                 title="Yellow & Red Cards — Top 15 Teams", color_discrete_sequence=["#ffd54a", "#ff5252"])
    st.plotly_chart(style_fig(fig, 400), use_container_width=True)

# ---------------- TAB 2: PLAYER EXPLORER ----------------
with tab2:
    st.markdown("### Search & Inspect Individual Players")
    label_lookup = fdf.sort_values("goals", ascending=False).drop_duplicates("player_label")
    sel_label = st.selectbox("Choose a player to inspect", label_lookup["player_label"].tolist())
    prow = fdf[fdf["player_label"] == sel_label].iloc[0]

    cinfo, cchart = st.columns([1, 1.4])
    with cinfo:
        st.markdown(f"""
        <div class="player-card">
        <h3>{prow['player']}</h3>
        <p style="color:#b9c4e6;">{prow['team']} · {prow['position']} · {prow['club']}</p>
        <hr>
        <p>🎂 <b>Age:</b> {prow['age_years']:.1f} years</p>
        <p>⚽ <b>Goals:</b> {int(prow['goals'])} &nbsp; | &nbsp; 🎯 <b>Assists:</b> {int(prow['assists'])}</p>
        <p>🥅 <b>Shots (on target):</b> {int(prow['shots'])} ({int(prow['shots_on_target'])})</p>
        <p>🕒 <b>Minutes:</b> {int(prow['minutes']) if pd.notna(prow['minutes']) else 0} over {int(prow['games'])} games ({int(prow['games_starts'])} starts)</p>
        <p>🟨 <b>Yellow / 🟥 Red:</b> {int(prow['cards_yellow'])} / {int(prow['cards_red'])}</p>
        <p>🛡️ <b>Tackles Won / Interceptions:</b> {int(prow['tackles_won'])} / {int(prow['interceptions'])}</p>
        </div>
        """, unsafe_allow_html=True)

    with cchart:
        per90_metrics = ["goals_per90", "assists_per90", "shots_per90", "shots_on_target_per90"]
        vals = prow[per90_metrics].fillna(0)
        fig = px.bar(x=[m.replace("_per90", "").replace("_", " ").title() for m in per90_metrics],
                     y=vals.values, title=f"{sel_label} — Per-90 Output",
                     color=vals.values, color_continuous_scale="Plasma")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_fig(fig, 340), use_container_width=True)

    st.markdown("#### All Players (filtered)")
    show_cols = ["player", "team", "position", "club", "age_years", "games", "games_starts",
                 "minutes", "goals", "assists", "goals_assists", "shots", "shots_on_target_pct",
                 "cards_yellow", "cards_red", "tackles_won", "interceptions"]
    st.dataframe(
        fdf[show_cols].rename(columns={
            "player": "Player", "team": "Team", "position": "Position", "club": "Club",
            "age_years": "Age", "games": "Games", "games_starts": "Starts", "minutes": "Minutes",
            "goals": "Goals", "assists": "Assists", "goals_assists": "G+A", "shots": "Shots",
            "shots_on_target_pct": "SoT %", "cards_yellow": "Yellow", "cards_red": "Red",
            "tackles_won": "Tackles Won", "interceptions": "Interceptions"
        }).sort_values("Goals", ascending=False),
        use_container_width=True, height=400
    )

# ---------------- TAB 3: TEAM COMPARISON ----------------
with tab3:
    st.markdown("### Compare Teams Head-to-Head")
    all_teams = sorted(fdf["team"].unique())
    default_teams = all_teams[:2] if len(all_teams) >= 2 else all_teams
    chosen_teams = st.multiselect("Select teams to compare", all_teams, default=default_teams)

    if chosen_teams:
        team_stats = fdf[fdf["team"].isin(chosen_teams)].groupby("team").agg(
            goals=("goals", "sum"), assists=("assists", "sum"),
            shots=("shots", "sum"), shots_on_target=("shots_on_target", "sum"),
            tackles_won=("tackles_won", "sum"), interceptions=("interceptions", "sum"),
            cards_yellow=("cards_yellow", "sum"), cards_red=("cards_red", "sum"),
            avg_age=("age_years", "mean"), squad_size=("player", "nunique"),
        ).reset_index()

        metrics = ["goals", "assists", "shots", "tackles_won", "interceptions"]
        fig = go.Figure()
        for i, t in enumerate(team_stats["team"]):
            fig.add_trace(go.Bar(name=t, x=metrics,
                                  y=team_stats.loc[team_stats["team"] == t, metrics].values.flatten(),
                                  marker_color=COLOR_SEQ[i % len(COLOR_SEQ)]))
        fig.update_layout(barmode="group", title="Team Metrics Comparison")
        st.plotly_chart(style_fig(fig), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(team_stats, x="team", y="avg_age", color="team",
                         title="Average Squad Age", color_discrete_sequence=COLOR_SEQ)
            st.plotly_chart(style_fig(fig), use_container_width=True)
        with c2:
            fig = px.bar(team_stats, x="team", y=["cards_yellow", "cards_red"], barmode="group",
                         title="Discipline: Cards by Team", color_discrete_sequence=["#ffd54a", "#ff5252"])
            st.plotly_chart(style_fig(fig), use_container_width=True)

        st.dataframe(team_stats, use_container_width=True)
    else:
        st.info("Select at least one team above to see comparisons.")

# ---------------- TAB 4: LEADERBOARDS ----------------
with tab4:
    st.markdown("### 🏅 Player Leaderboards")
    lb_options = {
        "Goals": "goals", "Assists": "assists", "Goals + Assists": "goals_assists",
        "Shots": "shots", "Shots on Target %": "shots_on_target_pct",
        "Tackles Won": "tackles_won", "Interceptions": "interceptions",
        "Crosses": "crosses", "Fouled": "fouled", "Yellow Cards": "cards_yellow",
        "Goals per 90": "goals_per90", "Assists per 90": "assists_per90",
    }
    lb_label = st.selectbox("Rank players by:", list(lb_options.keys()))
    lb_metric = lb_options[lb_label]

    lb = fdf[["player", "team", "position", lb_metric]].dropna(subset=[lb_metric])
    lb = lb.sort_values(lb_metric, ascending=False).head(15)

    fig = px.bar(lb, x=lb_metric, y="player", orientation="h", color=lb_metric,
                 color_continuous_scale="Plasma", title=f"Top 15 Players by {lb_label}",
                 hover_data=["team", "position"])
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(style_fig(fig, 500), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🅿️ Most Minutes Played")
        mins = fdf.sort_values("minutes", ascending=False)[["player", "team", "minutes"]].head(10)
        st.dataframe(mins.reset_index(drop=True), use_container_width=True)
    with c2:
        st.markdown("##### 🟥 Cards (Yellow + Red)")
        fdf["total_cards"] = fdf["cards_yellow"] + fdf["cards_red"] * 2
        cards = fdf.sort_values("total_cards", ascending=False)[["player", "team", "cards_yellow", "cards_red"]].head(10)
        st.dataframe(cards.reset_index(drop=True), use_container_width=True)

# ---------------- TAB 5: GOALKEEPERS & RADAR ----------------
with tab5:
    st.markdown("### 🧤 Goalkeeper Performance")
    gk_df = fdf[fdf["is_goalkeeper"] & (fdf["gk_games"] > 0)].copy()

    if not gk_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            top_gk = gk_df.sort_values("gk_save_pct", ascending=False).head(10)
            fig = px.bar(top_gk, x="gk_save_pct", y="player", orientation="h", color="gk_save_pct",
                         color_continuous_scale="Teal", title="Top 10 Goalkeepers by Save %",
                         hover_data=["team"])
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(style_fig(fig), use_container_width=True)
        with c2:
            top_cs = gk_df.sort_values("gk_clean_sheets", ascending=False).head(10)
            fig = px.bar(top_cs, x="gk_clean_sheets", y="player", orientation="h", color="gk_clean_sheets",
                         color_continuous_scale="Blues", title="Top 10 Goalkeepers by Clean Sheets",
                         hover_data=["team"])
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(style_fig(fig), use_container_width=True)

        st.dataframe(
            gk_df[["player", "team", "gk_games", "gk_minutes", "gk_goals_against", "gk_saves",
                   "gk_save_pct", "gk_clean_sheets", "gk_wins", "gk_ties", "gk_losses"]]
            .sort_values("gk_save_pct", ascending=False).reset_index(drop=True),
            use_container_width=True
        )
    else:
        st.info("No goalkeeper data available for the current filters.")

    st.markdown("---")
    st.markdown("### 🕸️ Multi-Player Radar Comparison (Outfield)")
    outfield = fdf[~fdf["is_goalkeeper"]]
    outfield_labels = outfield.drop_duplicates("player_label")
    radar_players = st.multiselect(
        "Pick up to 4 outfield players", sorted(outfield_labels["player_label"].tolist()), max_selections=4,
        default=list(outfield_labels.sort_values("goals", ascending=False)["player_label"].head(2))
    )

    radar_raw_metrics = ["goals_per90", "assists_per90", "shots_per90", "tackles_won", "interceptions", "crosses"]
    if radar_players:
        # normalize each metric to 0-100 scale (percentile within filtered outfield players) for fair comparison
        norm_df = outfield.copy()
        for m in radar_raw_metrics:
            mn, mx = norm_df[m].min(), norm_df[m].max()
            norm_df[m + "_norm"] = 0 if mx == mn else (norm_df[m] - mn) / (mx - mn) * 100

        fig = go.Figure()
        for i, p in enumerate(radar_players):
            prow = norm_df[norm_df["player_label"] == p][[m + "_norm" for m in radar_raw_metrics]].mean()
            fig.add_trace(go.Scatterpolar(
                r=prow.values, theta=[m.replace("_per90", " /90").replace("_", " ").title() for m in radar_raw_metrics],
                fill="toself", name=p, line_color=COLOR_SEQ[i % len(COLOR_SEQ)]
            ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100],
                                                       gridcolor="rgba(255,255,255,0.1)")),
                          title="Player Profile Comparison (percentile-normalized)", showlegend=True)
        st.plotly_chart(style_fig(fig, 550), use_container_width=True)
    else:
        st.info("Select at least one outfield player to display the radar chart.")

st.markdown("---")
st.caption("⚽ World Cup 2026 Player Stats Dashboard · Built with Streamlit & Plotly")