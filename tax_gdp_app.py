"""
Global Tax-to-GDP Analytics Dashboard
Data Source: World Bank Open Data (Indicator: GC.TAX.TOTL.GD.ZS)
Designed for tax policy experts and researchers.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from io import BytesIO

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Tax-to-GDP Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2044 0%, #1a3a6b 100%);
        color: #fff;
    }
    section[data-testid="stSidebar"] * { color: #e8eef8 !important; }
    section[data-testid="stSidebar"] .stMultiSelect > div { background: #1e3d73; border: 1px solid #3a6fcc; border-radius: 8px; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #fff !important; font-weight: 600; }

    /* Main area */
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }

    /* Header banner */
    .header-banner {
        background: linear-gradient(135deg, #0f2044 0%, #1a3a6b 60%, #1e5799 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-title { color: #ffffff; font-size: 1.9rem; font-weight: 700; margin: 0; }
    .header-sub { color: #a8c4e8; font-size: 0.95rem; margin-top: 0.3rem; }
    .header-badge {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.25);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #fff;
        font-size: 0.8rem;
        text-align: center;
    }

    /* Metric cards */
    .metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .metric-card {
        flex: 1; min-width: 160px;
        background: #ffffff;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 2px 12px rgba(15,32,68,0.08);
        border-left: 4px solid;
        transition: transform 0.15s;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(15,32,68,0.14); }
    .metric-card.blue  { border-color: #1a3a6b; }
    .metric-card.green { border-color: #1a7a3c; }
    .metric-card.amber { border-color: #d97706; }
    .metric-card.red   { border-color: #c0392b; }
    .metric-card.teal  { border-color: #0d7377; }
    .metric-label { font-size: 0.75rem; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.7rem; font-weight: 700; color: #0f2044; margin: 0.2rem 0; }
    .metric-sub   { font-size: 0.78rem; color: #9ca3af; }

    /* Section headers */
    .section-header {
        font-size: 1.1rem; font-weight: 700; color: #0f2044;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem; margin: 1.5rem 0 1rem;
        display: flex; align-items: center; gap: 0.5rem;
    }

    /* Info callout */
    .callout {
        background: #eff6ff; border-left: 4px solid #1a3a6b;
        border-radius: 0 8px 8px 0; padding: 0.9rem 1.2rem;
        font-size: 0.87rem; color: #1e3a5f; margin: 1rem 0;
    }
    .callout.amber {
        background: #fffbeb; border-color: #d97706; color: #7c4a00;
    }
    .callout.green {
        background: #f0fdf4; border-color: #1a7a3c; color: #14532d;
    }

    /* Insight card */
    .insight-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin: 1rem 0; }
    .insight-card {
        background: #fff; border-radius: 12px; padding: 1.2rem;
        box-shadow: 0 2px 10px rgba(15,32,68,0.07);
        border-top: 3px solid #1a3a6b;
    }
    .insight-title { font-weight: 700; color: #0f2044; font-size: 0.95rem; margin-bottom: 0.5rem; }
    .insight-text  { font-size: 0.84rem; color: #4b5563; line-height: 1.55; }

    /* Source footer */
    .source-footer {
        background: #f9fafb; border: 1px solid #e5e7eb;
        border-radius: 10px; padding: 0.9rem 1.2rem;
        font-size: 0.8rem; color: #6b7280; margin-top: 1.5rem;
        display: flex; align-items: center; gap: 0.6rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        background: #f1f5f9; border-radius: 8px 8px 0 0;
        font-weight: 600; color: #475569;
        border: 1px solid #e2e8f0; border-bottom: none;
        padding: 0.5rem 1.2rem;
    }
    .stTabs [aria-selected="true"] {
        background: #0f2044 !important; color: #fff !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: #0f2044; color: white; border-radius: 8px;
        border: none; font-weight: 600; padding: 0.5rem 1.5rem;
    }
    .stDownloadButton > button:hover { background: #1a3a6b; }

    /* Dataframe */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* India note badge */
    .india-note {
        background: #fff7ed; border: 1px solid #fed7aa;
        border-radius: 8px; padding: 0.7rem 1rem;
        font-size: 0.82rem; color: #7c2d12; margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
WB_INDICATOR  = "GC.TAX.TOTL.GD.ZS"
WB_BASE_URL   = "https://api.worldbank.org/v2"
DEFAULT_YEAR  = 2022

# Country registry: display name → ISO3 code, region, income group, India flag
COUNTRY_REGISTRY = {
    "India":          ("IND", "South Asia",          "Lower-Middle Income"),
    "China":          ("CHN", "East Asia & Pacific",  "Upper-Middle Income"),
    "Brazil":         ("BRA", "Latin America",        "Upper-Middle Income"),
    "South Africa":   ("ZAF", "Sub-Saharan Africa",   "Upper-Middle Income"),
    "Indonesia":      ("IDN", "East Asia & Pacific",  "Lower-Middle Income"),
    "Mexico":         ("MEX", "Latin America",        "Upper-Middle Income"),
    "Turkey":         ("TUR", "Europe & Central Asia","Upper-Middle Income"),
    "Argentina":      ("ARG", "Latin America",        "Upper-Middle Income"),
    "Nigeria":        ("NGA", "Sub-Saharan Africa",   "Lower-Middle Income"),
    "Kenya":          ("KEN", "Sub-Saharan Africa",   "Lower-Middle Income"),
    "Malaysia":       ("MYS", "East Asia & Pacific",  "Upper-Middle Income"),
    "Thailand":       ("THA", "East Asia & Pacific",  "Upper-Middle Income"),
    "South Korea":    ("KOR", "East Asia & Pacific",  "High Income"),
    "Japan":          ("JPN", "East Asia & Pacific",  "High Income"),
    "Singapore":      ("SGP", "East Asia & Pacific",  "High Income"),
    "Australia":      ("AUS", "East Asia & Pacific",  "High Income"),
    "Canada":         ("CAN", "North America",        "High Income"),
    "United States":  ("USA", "North America",        "High Income"),
    "United Kingdom": ("GBR", "Europe",               "High Income"),
    "Germany":        ("DEU", "Europe",               "High Income"),
    "France":         ("FRA", "Europe",               "High Income"),
    "Sweden":         ("SWE", "Europe",               "High Income"),
    "Denmark":        ("DNK", "Europe",               "High Income"),
    "Norway":         ("NOR", "Europe",               "High Income"),
    "Switzerland":    ("CHE", "Europe",               "High Income"),
    "Netherlands":    ("NLD", "Europe",               "High Income"),
    "Saudi Arabia":   ("SAU", "Middle East",          "High Income"),
    "UAE":            ("ARE", "Middle East",          "High Income"),
    "Pakistan":       ("PAK", "South Asia",           "Lower-Middle Income"),
    "Bangladesh":     ("BGD", "South Asia",           "Lower-Middle Income"),
}

ISO3_TO_ISO2 = {
    "IND":"IN","CHN":"CN","BRA":"BR","ZAF":"ZA","IDN":"ID","MEX":"MX","TUR":"TR",
    "ARG":"AR","NGA":"NG","KEN":"KE","MYS":"MY","THA":"TH","KOR":"KR","JPN":"JP",
    "SGP":"SG","AUS":"AU","CAN":"CA","USA":"US","GBR":"GB","DEU":"DE","FRA":"FR",
    "SWE":"SE","DNK":"DK","NOR":"NO","CHE":"CH","NLD":"NL","SAU":"SA","ARE":"AE",
    "PAK":"PK","BGD":"BD",
}

REGION_COLORS = {
    "South Asia":           "#e63946",
    "East Asia & Pacific":  "#457b9d",
    "Latin America":        "#2a9d8f",
    "Sub-Saharan Africa":   "#e9c46a",
    "Europe":               "#264653",
    "North America":        "#6d6875",
    "Europe & Central Asia":"#4a4e69",
    "Middle East":          "#f4a261",
}

PLOTLY_TEMPLATE = dict(
    layout=dict(
        font=dict(family="Inter, sans-serif", color="#1e293b"),
        paper_bgcolor="white",
        plot_bgcolor="#f8fafc",
        colorway=["#1a3a6b","#e63946","#2a9d8f","#e9c46a","#457b9d",
                  "#264653","#f4a261","#6d6875","#a8dadc","#c77dff"],
        xaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1", tickfont=dict(size=11)),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0",
                    borderwidth=1, font=dict(size=11)),
        margin=dict(l=50, r=30, t=60, b=50),
    )
)

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_world_bank_data(iso3_codes: list, start_year: int, end_year: int) -> pd.DataFrame:
    """Fetch Tax Revenue (% of GDP) from World Bank Open Data API."""
    code_str  = ";".join(iso3_codes)
    url = (f"{WB_BASE_URL}/country/{code_str}/indicator/{WB_INDICATOR}"
           f"?format=json&date={start_year}:{end_year}&per_page=2000")
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2 or not data[1]:
            return pd.DataFrame()
        records = []
        for item in data[1]:
            if item.get("value") is not None:
                records.append({
                    "ISO3":    item["country"]["id"],
                    "Country": item["country"]["value"],
                    "Year":    int(item["date"]),
                    "Tax_GDP": round(float(item["value"]), 2),
                })
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"World Bank API error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def get_latest_values(df: pd.DataFrame) -> pd.DataFrame:
    """Return each country's most recent available data point."""
    return (df.sort_values("Year", ascending=False)
              .groupby("ISO3").first().reset_index()
              [["ISO3","Country","Year","Tax_GDP"]])

def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    """Add Region and Income Group from registry."""
    name_map    = {v[0]: k    for k, v in COUNTRY_REGISTRY.items()}
    region_map  = {v[0]: v[1] for k, v in COUNTRY_REGISTRY.items()}
    income_map  = {v[0]: v[2] for k, v in COUNTRY_REGISTRY.items()}
    df = df.copy()
    df["DisplayName"]  = df["ISO3"].map(name_map).fillna(df["Country"])
    df["Region"]       = df["ISO3"].map(region_map).fillna("Other")
    df["IncomeGroup"]  = df["ISO3"].map(income_map).fillna("Unknown")
    return df

# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────
def chart_bar_comparison(df_latest: pd.DataFrame, highlight_country: str) -> go.Figure:
    df = df_latest.sort_values("Tax_GDP", ascending=True).copy()
    colors = []
    for _, row in df.iterrows():
        if row["DisplayName"] == highlight_country:
            colors.append("#e63946")
        elif row["IncomeGroup"] == "High Income":
            colors.append("#1a3a6b")
        elif row["IncomeGroup"] == "Upper-Middle Income":
            colors.append("#457b9d")
        else:
            colors.append("#a8c4e8")

    fig = go.Figure(go.Bar(
        x=df["Tax_GDP"], y=df["DisplayName"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=0.5)),
        text=[f"{v:.1f}%" for v in df["Tax_GDP"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Tax-to-GDP: %{x:.2f}%<br><extra></extra>",
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Tax Revenue as % of GDP — Country Comparison",
                   font=dict(size=15, color="#0f2044"), x=0.01),
        height=max(420, len(df) * 28),
        xaxis=dict(title="Tax Revenue (% of GDP)", range=[0, df["Tax_GDP"].max() * 1.15],
                   gridcolor="#e2e8f0"),
        yaxis=dict(title=""),
        bargap=0.35,
        showlegend=False,
    )
    # Add OECD average line
    oecd_avg = df[df["IncomeGroup"] == "High Income"]["Tax_GDP"].mean()
    fig.add_vline(x=oecd_avg, line_dash="dash", line_color="#d97706", line_width=1.5,
                  annotation_text=f"High-Income Avg: {oecd_avg:.1f}%",
                  annotation_position="top right",
                  annotation_font=dict(size=10, color="#d97706"))
    return fig

def chart_trend_lines(df: pd.DataFrame, selected_names: list) -> go.Figure:
    fig = go.Figure()
    palette = ["#1a3a6b","#e63946","#2a9d8f","#e9c46a","#457b9d",
               "#264653","#f4a261","#6d6875","#a8dadc","#c77dff",
               "#e76f51","#023e8a","#52b788","#f72585","#7209b7"]
    for i, name in enumerate(selected_names):
        sub = df[df["DisplayName"] == name].sort_values("Year")
        if sub.empty:
            continue
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=sub["Year"], y=sub["Tax_GDP"],
            mode="lines+markers", name=name,
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=color),
            hovertemplate=f"<b>{name}</b><br>Year: %{{x}}<br>Tax-to-GDP: %{{y:.2f}}%<extra></extra>",
        ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Tax-to-GDP Ratio — Historical Trend",
                   font=dict(size=15, color="#0f2044"), x=0.01),
        height=480,
        xaxis=dict(title="Year", gridcolor="#e2e8f0", dtick=2),
        yaxis=dict(title="Tax Revenue (% of GDP)", gridcolor="#e2e8f0"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

def chart_scatter_income(df_latest: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df_latest, x="Tax_GDP", y="DisplayName",
        color="Region", size="Tax_GDP",
        color_discrete_map=REGION_COLORS,
        hover_name="DisplayName",
        hover_data={"Tax_GDP": ":.2f", "IncomeGroup": True,
                    "Year": True, "DisplayName": False},
        labels={"Tax_GDP": "Tax Revenue (% of GDP)", "DisplayName": ""},
        title="Tax-to-GDP by Country — Coloured by Region",
        height=max(420, len(df_latest) * 28),
    )
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    fig.update_traces(marker=dict(line=dict(color="white", width=1)))
    return fig

def chart_box_income(df: pd.DataFrame) -> go.Figure:
    order = ["High Income", "Upper-Middle Income", "Lower-Middle Income", "Unknown"]
    palette = {"High Income": "#1a3a6b", "Upper-Middle Income": "#457b9d",
               "Lower-Middle Income": "#a8c4e8", "Unknown": "#e2e8f0"}
    fig = go.Figure()
    for grp in order:
        sub = df[df["IncomeGroup"] == grp]
        if sub.empty:
            continue
        fig.add_trace(go.Box(
            y=sub["Tax_GDP"], name=grp,
            marker_color=palette.get(grp, "#ccc"),
            boxmean="sd",
            hovertemplate="<b>" + grp + "</b><br>Tax-to-GDP: %{y:.2f}%<extra></extra>",
        ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Tax-to-GDP Distribution by Income Group",
                   font=dict(size=15, color="#0f2044"), x=0.01),
        height=420,
        yaxis=dict(title="Tax Revenue (% of GDP)"),
        xaxis=dict(title="Income Group"),
        showlegend=False,
    )
    return fig

def chart_choropleth(df_latest: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Choropleth(
        locations=df_latest["ISO3"],
        z=df_latest["Tax_GDP"],
        text=df_latest["DisplayName"],
        colorscale=[
            [0.0,  "#dbeafe"],
            [0.25, "#93c5fd"],
            [0.5,  "#3b82f6"],
            [0.75, "#1d4ed8"],
            [1.0,  "#1e3a8a"],
        ],
        colorbar=dict(title="Tax/GDP %", ticksuffix="%",
                      len=0.6, thickness=14,
                      bgcolor="rgba(255,255,255,0.8)"),
        hovertemplate="<b>%{text}</b><br>Tax-to-GDP: %{z:.2f}%<extra></extra>",
        marker_line_color="white", marker_line_width=0.5,
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        title=dict(text="Global Tax-to-GDP Heat Map",
                   font=dict(size=15, color="#0f2044"), x=0.01),
        geo=dict(showframe=False, showcoastlines=True,
                 coastlinecolor="#cbd5e1",
                 showland=True, landcolor="#f1f5f9",
                 showocean=True, oceancolor="#e0f2fe",
                 projection_type="natural earth",
                 bgcolor="white"),
        height=480,
        margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig

def chart_waterfall_india(df_india: pd.DataFrame) -> go.Figure:
    """Special chart showing India's Central vs General Govt adjusted ratio."""
    years = sorted(df_india["Year"].unique())[-10:]
    sub = df_india[df_india["Year"].isin(years)].sort_values("Year")
    central = sub["Tax_GDP"].values
    # State tax contribution is roughly 6.5–7.5% of GDP (PRS India 2024-25)
    state_contrib = np.full(len(central), 6.8)
    general = central + state_contrib

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Central Govt Tax/GDP", x=sub["Year"], y=central,
        marker_color="#1a3a6b",
        hovertemplate="Central only: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="State Govts Tax/GDP (est. +6.8%)", x=sub["Year"], y=state_contrib,
        marker_color="#a8c4e8",
        hovertemplate="State add-on: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="General Govt (OECD-comparable)", x=sub["Year"], y=general,
        mode="lines+markers",
        line=dict(color="#e63946", width=2.5, dash="dot"),
        marker=dict(size=7, color="#e63946"),
        hovertemplate="General Govt: %{y:.2f}%<extra></extra>",
    ))
    fig.add_hline(y=34.1, line_dash="dash", line_color="#6b7280", line_width=1.2,
                  annotation_text="OECD avg: 34.1%",
                  annotation_font=dict(size=10, color="#6b7280"),
                  annotation_position="bottom right")
    fig.add_hline(y=18.1, line_dash="dash", line_color="#2a9d8f", line_width=1.2,
                  annotation_text="Brazil: 18.1%",
                  annotation_font=dict(size=10, color="#2a9d8f"),
                  annotation_position="top right")
    fig.update_layout(
        **PLOTLY_TEMPLATE["layout"],
        barmode="stack",
        title=dict(text="India — Central vs General Government Tax-to-GDP (Methodological Breakdown)",
                   font=dict(size=14, color="#0f2044"), x=0.01),
        height=420,
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(title="Tax Revenue (% of GDP)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Controls")
    st.markdown("---")

    st.markdown("**🌍 Select Countries**")
    all_names     = sorted(COUNTRY_REGISTRY.keys())
    default_sel   = ["India","Brazil","South Africa","United States",
                     "United Kingdom","Germany","France","China",
                     "South Korea","Indonesia","Australia","Sweden"]
    selected_countries = st.multiselect(
        "", all_names, default=default_sel,
        help="Pick countries to compare. India is always included.",
    )
    if "India" not in selected_countries:
        selected_countries = ["India"] + selected_countries

    st.markdown("---")
    st.markdown("**📅 Year Range**")
    year_range = st.slider("", 2000, 2023, (2005, 2022), step=1)

    st.markdown("---")
    st.markdown("**🎯 Highlight Country**")
    highlight = st.selectbox("", selected_countries, index=0)

    st.markdown("---")
    st.markdown("**📊 Chart Style**")
    show_map   = st.checkbox("Show World Map", value=True)
    show_india = st.checkbox("Show India Methodology Deep-Dive", value=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; color:#a8c4e8; line-height:1.6;'>
    📌 <b>Data Source</b><br>
    World Bank Open Data<br>
    Indicator: GC.TAX.TOTL.GD.ZS<br>
    <i>Tax revenue (% of GDP)</i><br><br>
    🔄 Cache refreshes every hour<br><br>
    ⚠️ India figures = Central Govt only<br>
    (See India Deep-Dive tab)
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOAD
# ─────────────────────────────────────────────────────────────────────────────
iso3_list = [COUNTRY_REGISTRY[c][0] for c in selected_countries if c in COUNTRY_REGISTRY]

with st.spinner("⏳ Fetching data from World Bank Open Data API..."):
    raw_df = fetch_world_bank_data(iso3_list, year_range[0], year_range[1])

if raw_df.empty:
    st.error("⚠️ Could not fetch data from World Bank API. Please check your internet connection.")
    st.stop()

df_all    = enrich_df(raw_df)
df_latest = enrich_df(get_latest_values(raw_df))

# India-specific subset
df_india  = df_all[df_all["ISO3"] == "IND"].copy()

# Comparison year subset
comp_year_options = sorted(df_all["Year"].unique(), reverse=True)
comp_year = comp_year_options[0] if comp_year_options else DEFAULT_YEAR
df_comp   = df_all[df_all["Year"] == comp_year]
if df_comp.empty and len(comp_year_options) > 1:
    comp_year = comp_year_options[1]
    df_comp = df_all[df_all["Year"] == comp_year]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="header-banner">
    <div>
        <div class="header-title">🌐 Global Tax-to-GDP Analytics Dashboard</div>
        <div class="header-sub">
            Comparative tax policy intelligence for researchers, economists & tax professionals
        </div>
    </div>
    <div style="display:flex; gap:0.75rem; flex-wrap:wrap; justify-content:flex-end;">
        <div class="header-badge">📦 World Bank Open Data<br><small>GC.TAX.TOTL.GD.ZS</small></div>
        <div class="header-badge">🗓️ {year_range[0]}–{year_range[1]}<br><small>Selected Range</small></div>
        <div class="header-badge">🌍 {len(selected_countries)} Countries<br><small>Selected</small></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# KPI METRICS ROW
# ─────────────────────────────────────────────────────────────────────────────
india_row  = df_latest[df_latest["ISO3"] == "IND"]
india_val  = india_row["Tax_GDP"].values[0] if not india_row.empty else None
india_yr   = int(india_row["Year"].values[0]) if not india_row.empty else "—"
hi_avg     = df_latest[df_latest["IncomeGroup"] == "High Income"]["Tax_GDP"].mean()
lmi_avg    = df_latest[df_latest["IncomeGroup"] == "Lower-Middle Income"]["Tax_GDP"].mean()
max_row    = df_latest.loc[df_latest["Tax_GDP"].idxmax()]
min_row    = df_latest.loc[df_latest["Tax_GDP"].idxmin()]
median_val = df_latest["Tax_GDP"].median()

cards_html = f"""
<div class="metric-row">
  <div class="metric-card blue">
    <div class="metric-label">India (Central Govt)</div>
    <div class="metric-value">{india_val:.1f}%</div>
    <div class="metric-sub">FY {india_yr} · World Bank</div>
  </div>
  <div class="metric-card green">
    <div class="metric-label">India (General Govt est.)</div>
    <div class="metric-value">~{(india_val+6.8):.1f}%</div>
    <div class="metric-sub">Centre + States (OECD basis)</div>
  </div>
  <div class="metric-card amber">
    <div class="metric-label">High-Income Country Avg</div>
    <div class="metric-value">{hi_avg:.1f}%</div>
    <div class="metric-sub">Selected high-income peers</div>
  </div>
  <div class="metric-card red">
    <div class="metric-label">Highest in Selection</div>
    <div class="metric-value">{max_row['Tax_GDP']:.1f}%</div>
    <div class="metric-sub">{max_row['DisplayName']}</div>
  </div>
  <div class="metric-card teal">
    <div class="metric-label">Median (Selected)</div>
    <div class="metric-value">{median_val:.1f}%</div>
    <div class="metric-sub">{len(df_latest)} countries</div>
  </div>
</div>
"""
st.markdown(cards_html, unsafe_allow_html=True)

# Methodology callout
st.markdown("""
<div class="callout amber">
  ⚠️ <b>Methodology Note (India):</b> World Bank reports India's <i>Central Government</i> tax ratio only (~11–12% of GDP).
  This excludes State-level taxes (SGST, VAT, Stamp Duty, State Excise). On an OECD-comparable
  <i>General Government</i> basis (Centre + States), India's ratio rises to approximately <b>18–20% of GDP</b>
  — comparable to Brazil (18.1%) and other emerging market peers. See the <b>India Deep-Dive</b> tab for details.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Country Comparison",
    "📈 Trend Analysis",
    "🗺️ World Map",
    "🇮🇳 India Deep-Dive",
    "📋 Data & Download",
])

# ── TAB 1: COUNTRY COMPARISON ────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f'<div class="section-header">📊 Latest Available Data vs Peers (Year: {comp_year})</div>',
                    unsafe_allow_html=True)
        fig_bar = chart_bar_comparison(df_comp, highlight)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.markdown('<div class="section-header">🏆 Rankings</div>', unsafe_allow_html=True)
        ranked = df_comp.sort_values("Tax_GDP", ascending=False).reset_index(drop=True)
        ranked.index += 1
        for _, row in ranked.iterrows():
            medal = "🥇" if _ == 1 else ("🥈" if _ == 2 else ("🥉" if _ == 3 else f"{_}."))
            bg = "#fff7ed" if row["DisplayName"] == highlight else "#f8fafc"
            st.markdown(f"""
            <div style='background:{bg};border-radius:8px;padding:0.4rem 0.7rem;
                        margin-bottom:0.3rem;font-size:0.83rem;'>
              <span style='font-weight:700;color:#0f2044;'>{medal} {row['DisplayName']}</span><br>
              <span style='color:#6b7280;'>{row['Tax_GDP']:.1f}% · {row['IncomeGroup']}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">📦 Distribution by Income Group</div>', unsafe_allow_html=True)
    fig_box = chart_box_income(df_comp)
    st.plotly_chart(fig_box, use_container_width=True)

# ── TAB 2: TREND ANALYSIS ────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">📈 Historical Tax-to-GDP Trends</div>', unsafe_allow_html=True)
    fig_trend = chart_trend_lines(df_all, selected_countries)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown('<div class="section-header">🔍 Regional Scatter View</div>', unsafe_allow_html=True)
    fig_scatter = chart_scatter_income(df_comp)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # CAGR table
    st.markdown('<div class="section-header">📐 Change Analysis — First vs Latest Year</div>',
                unsafe_allow_html=True)
    cagr_rows = []
    for c in selected_countries:
        iso = COUNTRY_REGISTRY.get(c, (None,))[0]
        sub = df_all[df_all["ISO3"] == iso].sort_values("Year")
        if len(sub) >= 2:
            first, last = sub.iloc[0], sub.iloc[-1]
            change  = last["Tax_GDP"] - first["Tax_GDP"]
            n_years = last["Year"] - first["Year"]
            cagr    = ((last["Tax_GDP"] / first["Tax_GDP"]) ** (1/n_years) - 1) * 100 if n_years > 0 and first["Tax_GDP"] > 0 else None
            cagr_rows.append({
                "Country":        c,
                f"Tax/GDP ({int(first['Year'])})": f"{first['Tax_GDP']:.1f}%",
                f"Tax/GDP ({int(last['Year'])})":  f"{last['Tax_GDP']:.1f}%",
                "Absolute Change": f"{change:+.1f} pp",
                "CAGR":           f"{cagr:+.2f}%/yr" if cagr else "—",
            })
    if cagr_rows:
        cagr_df = pd.DataFrame(cagr_rows)
        st.dataframe(cagr_df, use_container_width=True, hide_index=True)

# ── TAB 3: WORLD MAP ─────────────────────────────────────────────────────────
with tab3:
    if show_map:
        st.markdown('<div class="section-header">🗺️ Global Tax-to-GDP Heat Map</div>',
                    unsafe_allow_html=True)
        fig_map = chart_choropleth(df_latest)
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown("""
        <div class="callout">
          🔵 <b>Darker blue = higher tax-to-GDP ratio.</b> Lighter shades indicate lower ratios, common
          in emerging economies and resource-dependent states. North-western Europe consistently
          shows the deepest concentration. Map shows most recent available year per country.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Enable 'Show World Map' in the sidebar to view this chart.")

# ── TAB 4: INDIA DEEP-DIVE ───────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">🇮🇳 India — Methodological Deep-Dive</div>',
                unsafe_allow_html=True)

    if not df_india.empty and show_india:
        fig_india = chart_waterfall_india(df_india)
        st.plotly_chart(fig_india, use_container_width=True)

    st.markdown("""
    <div class="callout amber">
      <b>Why the Central-only figure understates India's fiscal effort:</b><br><br>
      The World Bank's <code>GC.TAX.TOTL.GD.ZS</code> indicator for India captures only the
      <b>Central Government's gross tax receipts</b> — personal income tax, corporate tax,
      customs, central excise, CGST, and IGST collected by the Centre. It <b>excludes</b>:<br><br>
      • <b>SGST</b> (≈44% of state own-tax revenue)<br>
      • <b>VAT / Sales Tax</b> on petroleum & alcohol<br>
      • <b>Stamp Duty & Registration fees</b><br>
      • <b>State Excise</b> on liquor<br>
      • <b>Property taxes</b> and vehicle taxes<br><br>
      The OECD methodology, by contrast, uses <b>General Government</b> figures that consolidate
      all levels of government. On this basis, India's combined ratio is approximately
      <b>18–20% of GDP</b> — placing it alongside Brazil (18.1%) as an emerging-market peer,
      not at "half the OECD average" as a Central-only comparison implies.
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="insight-card">
          <div class="insight-title">📌 Central Govt Tax Components</div>
          <div class="insight-text">
            <b>Personal Income Tax:</b> ₹12.90 lakh cr (FY25)<br>
            <b>Corporate Tax:</b> ₹12.40 lakh cr<br>
            <b>GST (CGST + IGST):</b> Part of ₹22.08 lakh cr total<br>
            <b>STT:</b> ₹53,095 cr (+55.6% YoY)<br>
            <b>Customs + Excise:</b> Balance<br><br>
            <i>Total Gross Direct Tax: ₹25.87 lakh cr (+22.19%)</i>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="insight-card">
          <div class="insight-title">🏛️ State Tax Revenue Components</div>
          <div class="insight-text">
            <b>SGST:</b> ~44% of state own-tax revenue<br>
            <b>Sales Tax / VAT:</b> ~21%<br>
            <b>State Excise (liquor):</b> ~14%<br>
            <b>Stamp Duty:</b> ~12% (MH, UP, Haryana 14–18%)<br>
            <b>Vehicles + Electricity:</b> ~10%<br><br>
            <i>Combined state contribution ≈ 6.5–7.5% of GDP</i><br>
            <i>Source: PRS India – State of State Finances 2024-25</i>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="callout green">
      <b>Policy implication:</b> India's tax-to-GDP ratio, correctly measured, is not dramatically
      below peer emerging economies. The more critical debate is about <b>efficiency of expenditure,
      breadth of the formal tax base</b> (only ~2.2% of the population actually pays income tax),
      <b>compliance burden on MSMEs</b>, and the <b>cascading taxation</b> of savings through
      Income Tax → GST → STT → LTCG — all of which affect taxpayer trust irrespective of the
      aggregate ratio.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 5: DATA TABLE & DOWNLOAD ─────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">📋 Full Data Table</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_income = st.multiselect("Filter by Income Group",
                                       df_all["IncomeGroup"].unique().tolist(),
                                       default=df_all["IncomeGroup"].unique().tolist())
    with col_f2:
        filter_region = st.multiselect("Filter by Region",
                                       df_all["Region"].unique().tolist(),
                                       default=df_all["Region"].unique().tolist())
    with col_f3:
        sort_col = st.selectbox("Sort by", ["Tax_GDP","Year","DisplayName"], index=0)

    filtered = df_all[
        (df_all["IncomeGroup"].isin(filter_income)) &
        (df_all["Region"].isin(filter_region))
    ].sort_values(sort_col, ascending=(sort_col == "DisplayName"))

    display_cols = ["DisplayName","ISO3","Year","Tax_GDP","Region","IncomeGroup"]
    rename_map   = {"DisplayName":"Country","Tax_GDP":"Tax/GDP (%)","IncomeGroup":"Income Group"}
    st.dataframe(
        filtered[display_cols].rename(columns=rename_map),
        use_container_width=True, hide_index=True, height=380,
    )

    # Summary stats
    st.markdown('<div class="section-header">📐 Summary Statistics (Latest Year)</div>',
                unsafe_allow_html=True)
    stats = df_latest.groupby("IncomeGroup")["Tax_GDP"].agg(
        Count="count", Mean="mean", Median="median", Min="min", Max="max", Std="std"
    ).round(2).reset_index()
    stats.columns = ["Income Group","Countries","Mean %","Median %","Min %","Max %","Std Dev"]
    st.dataframe(stats, use_container_width=True, hide_index=True)

    # Download
    st.markdown("---")
    csv_data = filtered[display_cols].rename(columns=rename_map).to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Data as CSV",
        data=csv_data,
        file_name="tax_gdp_data_worldbank.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────────────────────────────────────
# AUTO-GENERATED INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">💡 Key Analytical Insights</div>', unsafe_allow_html=True)

if india_val:
    gap_hi   = hi_avg - india_val
    top3     = df_latest.nlargest(3, "Tax_GDP")[["DisplayName","Tax_GDP"]].values
    bottom3  = df_latest.nsmallest(3, "Tax_GDP")[["DisplayName","Tax_GDP"]].values
    trending_up = []
    trending_dn = []
    for c in selected_countries:
        iso = COUNTRY_REGISTRY.get(c, (None,))[0]
        sub = df_all[df_all["ISO3"] == iso].sort_values("Year")
        if len(sub) >= 5:
            recent = sub.tail(5)["Tax_GDP"]
            slope  = np.polyfit(range(len(recent)), recent, 1)[0]
            if slope > 0.2:
                trending_up.append(c)
            elif slope < -0.2:
                trending_dn.append(c)

    insights_html = f"""
    <div class="insight-grid">
      <div class="insight-card">
        <div class="insight-title">🇮🇳 India vs High-Income Average</div>
        <div class="insight-text">
          India's Central Govt ratio of <b>{india_val:.1f}%</b> is <b>{gap_hi:.1f} percentage points</b>
          below the selected high-income country average of {hi_avg:.1f}%.
          On a general government (OECD-comparable) basis, this gap narrows significantly
          to approximately <b>{hi_avg - (india_val+6.8):.1f} pp</b>.
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">🏆 Highest Ratios in Selection</div>
        <div class="insight-text">
          {'<br>'.join([f"<b>{r[0]}</b>: {r[1]:.1f}%" for r in top3])}
          <br><br><i>High ratios are typical of Nordic welfare-state models with broad
          social security coverage funded by high personal and corporate taxes.</i>
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">📉 Lowest Ratios in Selection</div>
        <div class="insight-text">
          {'<br>'.join([f"<b>{r[0]}</b>: {r[1]:.1f}%" for r in bottom3])}
          <br><br><i>Low ratios often reflect large informal economies, resource-revenue
          dependence, or deliberate low-tax policy frameworks (e.g. UAE, Singapore).</i>
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">📈 Trending Up (Last 5 Yrs)</div>
        <div class="insight-text">
          {', '.join(trending_up) if trending_up else 'No strong upward trends detected.'}
          <br><br><i>Rising ratios may reflect formalisation of the economy, improved
          compliance infrastructure, or expansion of the tax base.</i>
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">📉 Trending Down (Last 5 Yrs)</div>
        <div class="insight-text">
          {', '.join(trending_dn) if trending_dn else 'No strong downward trends detected.'}
          <br><br><i>Falling ratios may indicate tax reform, economic slowdown, or
          deliberate policy choices to boost competitiveness.</i>
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-title">⚖️ The Emerging Market Context</div>
        <div class="insight-text">
          Among selected upper-middle income countries, the median Tax/GDP is
          <b>{df_latest[df_latest['IncomeGroup']=='Upper-Middle Income']['Tax_GDP'].median():.1f}%</b>.
          Structural barriers — large informal sectors, agriculture exemptions,
          and weak enforcement capacity — are common constraints across this peer group.
        </div>
      </div>
    </div>
    """
    st.markdown(insights_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SOURCE FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="source-footer">
  <span style='font-size:1.2rem;'>📦</span>
  <div>
    <b>Primary Data Source:</b>
    World Bank Open Data — Indicator <code>GC.TAX.TOTL.GD.ZS</code>:
    <i>Tax revenue (% of GDP)</i> |
    <a href="https://data.worldbank.org/indicator/GC.TAX.TOTL.GD.ZS" target="_blank">
    data.worldbank.org</a> &nbsp;|&nbsp;
    <b>Supplementary:</b> PRS India – State of State Finances 2024-25 ·
    OECD Revenue Statistics 2025 · IMF Fiscal Monitor ·
    CBDT Annual Report FY 2024-25 &nbsp;|&nbsp;
    <b>Last API Fetch:</b> Live (cached 1 hr) &nbsp;|&nbsp;
    <b>Note:</b> India Central Govt only in WB data; general govt estimate = +6.8 pp (state taxes).
  </div>
</div>
""", unsafe_allow_html=True)
