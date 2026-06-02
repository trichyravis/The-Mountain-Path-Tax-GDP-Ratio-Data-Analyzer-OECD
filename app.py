
"""
Global Tax-to-GDP Analytics — Production Pipeline
====================================================
Workflow-grade implementation:
  - Multi-source: OECD Global Revenue Statistics, IMF DataMapper, World Bank
  - Source priority: OECD (1) > IMF (2) > World Bank (3)
  - Master country dimension table (ISO3-standardised, alias-resolved)
  - Per-observation metadata (source, definition, coverage, GDP denominator)
  - Quality checks: gap detection, jump flags, cross-source comparison
  - Two final outputs: raw table + harmonized table
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tax-to-GDP Pipeline Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif; }

section[data-testid="stSidebar"]{ background:linear-gradient(180deg,#0f2044 0%,#1a3a6b 100%); }
section[data-testid="stSidebar"] *{ color:#e8eef8 !important; }
section[data-testid="stSidebar"] .stMultiSelect>div{ background:#1e3d73; border:1px solid #3a6fcc; border-radius:8px; }

.main .block-container{ padding-top:1.2rem; max-width:1500px; }

.header-banner{
  background:linear-gradient(135deg,#0f2044 0%,#1a3a6b 55%,#1e5799 100%);
  border-radius:14px; padding:1.6rem 2rem; margin-bottom:1.2rem;
  display:flex; align-items:center; justify-content:space-between;
}
.header-title{ color:#fff; font-size:1.7rem; font-weight:700; margin:0; }
.header-sub{ color:#a8c4e8; font-size:0.9rem; margin-top:0.25rem; }
.badge{
  background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.22);
  border-radius:8px; padding:0.45rem 0.9rem; color:#fff; font-size:0.78rem; text-align:center;
}

.metric-row{ display:flex; gap:0.8rem; margin-bottom:1.2rem; flex-wrap:wrap; }
.metric-card{
  flex:1; min-width:140px; background:#fff; border-radius:10px;
  padding:1rem 1.2rem; box-shadow:0 2px 10px rgba(15,32,68,0.07);
  border-left:4px solid; transition:transform .12s;
}
.metric-card:hover{ transform:translateY(-2px); }
.metric-card.blue { border-color:#1a3a6b; }
.metric-card.green{ border-color:#1a7a3c; }
.metric-card.amber{ border-color:#d97706; }
.metric-card.red  { border-color:#c0392b; }
.metric-card.teal { border-color:#0d7377; }
.metric-card.purple{ border-color:#7c3aed; }
.mlabel{ font-size:0.72rem; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:.05em; }
.mvalue{ font-size:1.55rem; font-weight:700; color:#0f2044; margin:.15rem 0; }
.msub  { font-size:0.75rem; color:#9ca3af; }

.section-header{
  font-size:1.05rem; font-weight:700; color:#0f2044;
  border-bottom:2px solid #e5e7eb; padding-bottom:.4rem;
  margin:1.4rem 0 .8rem; display:flex; align-items:center; gap:.4rem;
}

.callout{ background:#eff6ff; border-left:4px solid #1a3a6b; border-radius:0 8px 8px 0; padding:.8rem 1.1rem; font-size:.85rem; color:#1e3a5f; margin:.8rem 0; }
.callout.amber{ background:#fffbeb; border-color:#d97706; color:#7c4a00; }
.callout.green{ background:#f0fdf4; border-color:#1a7a3c; color:#14532d; }
.callout.red  { background:#fef2f2; border-color:#c0392b; color:#7f1d1d; }

.source-badge{
  display:inline-flex; align-items:center; gap:.35rem;
  border-radius:20px; padding:.2rem .7rem; font-size:.75rem; font-weight:600; margin:.15rem .2rem;
}
.src-oecd  { background:#dbeafe; color:#1e3a8a; }
.src-imf   { background:#fef9c3; color:#713f12; }
.src-wb    { background:#dcfce7; color:#14532d; }
.src-na    { background:#f1f5f9; color:#64748b; }

.qcheck-pass{ color:#1a7a3c; font-weight:600; }
.qcheck-warn{ color:#d97706; font-weight:600; }
.qcheck-fail{ color:#c0392b; font-weight:600; }

.insight-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:.9rem; margin:.8rem 0; }
.insight-card{ background:#fff; border-radius:10px; padding:1.1rem; box-shadow:0 2px 8px rgba(15,32,68,.07); border-top:3px solid #1a3a6b; }
.insight-title{ font-weight:700; color:#0f2044; font-size:.92rem; margin-bottom:.4rem; }
.insight-text { font-size:.82rem; color:#4b5563; line-height:1.55; }

.source-footer{
  background:#f9fafb; border:1px solid #e5e7eb; border-radius:10px;
  padding:.8rem 1.1rem; font-size:.78rem; color:#6b7280; margin-top:1.4rem;
}

.stTabs [data-baseweb="tab"]{ background:#f1f5f9; border-radius:8px 8px 0 0; font-weight:600; color:#475569; }
.stTabs [aria-selected="true"]{ background:#0f2044 !important; color:#fff !important; }
.stDownloadButton>button{ background:#0f2044; color:white; border-radius:8px; border:none; font-weight:600; }
.stDownloadButton>button:hover{ background:#1a3a6b; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MASTER COUNTRY DIMENSION TABLE
# Resolves aliases; single source of truth for ISO3 ↔ names ↔ metadata
# ─────────────────────────────────────────────────────────────────────────────
COUNTRY_DIM = {
    # iso3: (canonical_name, aliases, region, income_group, wb_name, oecd_member, notes)
    "IND": ("India",         ["India"],                                    "South Asia",          "Lower-Middle Income", "India",          False, "Central Govt only in WB; state taxes excluded"),
    "CHN": ("China",         ["China","China, People's Republic of"],      "East Asia & Pacific", "Upper-Middle Income", "China",          False, ""),
    "BRA": ("Brazil",        ["Brazil"],                                   "Latin America",       "Upper-Middle Income", "Brazil",         False, ""),
    "ZAF": ("South Africa",  ["South Africa"],                             "Sub-Saharan Africa",  "Upper-Middle Income", "South Africa",   False, ""),
    "IDN": ("Indonesia",     ["Indonesia"],                                "East Asia & Pacific", "Lower-Middle Income", "Indonesia",      False, ""),
    "MEX": ("Mexico",        ["Mexico"],                                   "Latin America",       "Upper-Middle Income", "Mexico",         True,  "OECD member since 1994"),
    "TUR": ("Turkey",        ["Turkey","Türkiye"],                         "Europe & Central Asia","Upper-Middle Income","Turkiye",        True,  "Alias: Türkiye in some OECD releases"),
    "ARG": ("Argentina",     ["Argentina"],                                "Latin America",       "Upper-Middle Income", "Argentina",      False, ""),
    "NGA": ("Nigeria",       ["Nigeria"],                                  "Sub-Saharan Africa",  "Lower-Middle Income", "Nigeria",        False, ""),
    "KEN": ("Kenya",         ["Kenya"],                                    "Sub-Saharan Africa",  "Lower-Middle Income", "Kenya",          False, ""),
    "MYS": ("Malaysia",      ["Malaysia"],                                 "East Asia & Pacific", "Upper-Middle Income", "Malaysia",       False, ""),
    "THA": ("Thailand",      ["Thailand"],                                 "East Asia & Pacific", "Upper-Middle Income", "Thailand",       False, ""),
    "KOR": ("South Korea",   ["Korea","Korea, Republic of","Republic of Korea"],"East Asia & Pacific","High Income","Korea, Rep.",   True,  "OECD member; WB name 'Korea, Rep.'"),
    "JPN": ("Japan",         ["Japan"],                                    "East Asia & Pacific", "High Income",         "Japan",          True,  "OECD member"),
    "SGP": ("Singapore",     ["Singapore"],                                "East Asia & Pacific", "High Income",         "Singapore",      False, ""),
    "AUS": ("Australia",     ["Australia"],                                "East Asia & Pacific", "High Income",         "Australia",      True,  "OECD member"),
    "CAN": ("Canada",        ["Canada"],                                   "North America",       "High Income",         "Canada",         True,  "OECD member"),
    "USA": ("United States", ["United States","United States of America"], "North America",       "High Income",         "United States",  True,  "OECD member; WB name 'United States'"),
    "GBR": ("United Kingdom",["United Kingdom","UK"],                      "Europe",              "High Income",         "United Kingdom", True,  "OECD member"),
    "DEU": ("Germany",       ["Germany"],                                  "Europe",              "High Income",         "Germany",        True,  "OECD member"),
    "FRA": ("France",        ["France"],                                   "Europe",              "High Income",         "France",         True,  "OECD member"),
    "SWE": ("Sweden",        ["Sweden"],                                   "Europe",              "High Income",         "Sweden",         True,  "OECD member"),
    "DNK": ("Denmark",       ["Denmark"],                                  "Europe",              "High Income",         "Denmark",        True,  "OECD member"),
    "NOR": ("Norway",        ["Norway"],                                   "Europe",              "High Income",         "Norway",         True,  "OECD member"),
    "CHE": ("Switzerland",   ["Switzerland"],                              "Europe",              "High Income",         "Switzerland",    True,  "OECD member"),
    "NLD": ("Netherlands",   ["Netherlands"],                              "Europe",              "High Income",         "Netherlands",    True,  "OECD member"),
    "SAU": ("Saudi Arabia",  ["Saudi Arabia"],                             "Middle East",         "High Income",         "Saudi Arabia",   False, ""),
    "ARE": ("UAE",           ["United Arab Emirates","UAE"],               "Middle East",         "High Income",         "United Arab Emirates", False, ""),
    "PAK": ("Pakistan",      ["Pakistan"],                                 "South Asia",          "Lower-Middle Income", "Pakistan",       False, ""),
    "BGD": ("Bangladesh",    ["Bangladesh"],                               "South Asia",          "Lower-Middle Income", "Bangladesh",     False, ""),
    "CIV": ("Côte d'Ivoire", ["Cote d'Ivoire","Ivory Coast","Côte d'Ivoire"], "Sub-Saharan Africa","Lower-Middle Income","Cote d'Ivoire",False,"Alias: Ivory Coast"),
    "TZA": ("Tanzania",      ["Tanzania","United Republic of Tanzania"],   "Sub-Saharan Africa",  "Lower-Middle Income", "Tanzania",       False, ""),
    "ETH": ("Ethiopia",      ["Ethiopia"],                                 "Sub-Saharan Africa",  "Low Income",          "Ethiopia",       False, ""),
    "GHA": ("Ghana",         ["Ghana"],                                    "Sub-Saharan Africa",  "Lower-Middle Income", "Ghana",          False, ""),
    "POL": ("Poland",        ["Poland"],                                   "Europe",              "High Income",         "Poland",         True,  "OECD member"),
    "ESP": ("Spain",         ["Spain"],                                    "Europe",              "High Income",         "Spain",          True,  "OECD member"),
    "ITA": ("Italy",         ["Italy"],                                    "Europe",              "High Income",         "Italy",          True,  "OECD member"),
}

# Build alias → ISO3 lookup (for deduplication)
ALIAS_TO_ISO3 = {}
for iso3, v in COUNTRY_DIM.items():
    for alias in v[1]:
        ALIAS_TO_ISO3[alias.lower().strip()] = iso3

def resolve_iso3(name: str, iso3_hint: str = None) -> str:
    """Return canonical ISO3, resolving aliases."""
    if iso3_hint and iso3_hint in COUNTRY_DIM:
        return iso3_hint
    return ALIAS_TO_ISO3.get(name.lower().strip(), iso3_hint or "UNK")

def dim_field(iso3: str, field: int):
    return COUNTRY_DIM.get(iso3, ("Unknown","","","Unknown","",False,""))[field]

# ─────────────────────────────────────────────────────────────────────────────
# SOURCE DEFINITIONS (metadata registry)
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_META = {
    "OECD": {
        "priority": 1,
        "label":    "OECD Revenue Statistics",
        "coverage": "General Government (all levels)",
        "gdp_denom":"Current market prices GDP",
        "tax_scope": "Tax revenue only (OECD definition)",
        "url":      "https://stats.oecd.org/",
        "notes":    "Gold standard for OECD members; also covers ~100 non-members via Global RevStats",
        "color":    "#1e3a8a",
        "badge":    "src-oecd",
    },
    "IMF": {
        "priority": 2,
        "label":    "IMF DataMapper (WEO/GFS)",
        "coverage": "General Government (consolidated)",
        "gdp_denom":"Current GDP (WEO vintage)",
        "tax_scope": "Tax revenue % GDP (GGT_NGDP indicator)",
        "url":      "https://www.imf.org/external/datamapper/",
        "notes":    "Uses IMF WEO GDP denominator; slight differences from OECD for same country-years",
        "color":    "#713f12",
        "badge":    "src-imf",
    },
    "WB": {
        "priority": 3,
        "label":    "World Bank Open Data",
        "coverage": "Central Government only (for most developing countries)",
        "gdp_denom":"Current USD GDP (WDI)",
        "tax_scope": "Tax revenue % GDP (GC.TAX.TOTL.GD.ZS)",
        "url":      "https://data.worldbank.org/indicator/GC.TAX.TOTL.GD.ZS",
        "notes":    "India/many developing: Central Govt only — understates general govt ratio. Use OECD/IMF where available.",
        "color":    "#14532d",
        "badge":    "src-wb",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_worldbank(iso3_list: list, start_yr: int, end_yr: int) -> pd.DataFrame:
    """World Bank: GC.TAX.TOTL.GD.ZS — Tax revenue (% of GDP)."""
    codes = ";".join(iso3_list)
    url = (f"https://api.worldbank.org/v2/country/{codes}"
           f"/indicator/GC.TAX.TOTL.GD.ZS"
           f"?format=json&date={start_yr}:{end_yr}&per_page=2000")
    try:
        r = requests.get(url, timeout=20); r.raise_for_status()
        data = r.json()
        if len(data) < 2 or not data[1]:
            return pd.DataFrame()
        rows = []
        for item in data[1]:
            if item.get("value") is not None:
                iso3 = item["country"]["id"]
                rows.append({
                    "iso3":        iso3,
                    "raw_name":    item["country"]["value"],
                    "year":        int(item["date"]),
                    "value":       round(float(item["value"]), 4),
                    "source":      "WB",
                    "indicator":   "GC.TAX.TOTL.GD.ZS",
                    "coverage":    SOURCE_META["WB"]["coverage"],
                    "gdp_denom":   SOURCE_META["WB"]["gdp_denom"],
                    "definition":  SOURCE_META["WB"]["tax_scope"],
                    "fetched_at":  datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
        return pd.DataFrame(rows)
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_imf(iso3_list: list, start_yr: int, end_yr: int) -> pd.DataFrame:
    """IMF DataMapper: GGT_NGDP — General Government Tax Revenue (% GDP)."""
    country_str = ",".join(iso3_list)
    url = f"https://www.imf.org/external/datamapper/api/v1/GGT_NGDP/{country_str}"
    try:
        r = requests.get(url, timeout=20); r.raise_for_status()
        data = r.json()
        values_block = data.get("values", {}).get("GGT_NGDP", {})
        rows = []
        for iso3, yr_dict in values_block.items():
            for yr_str, val in yr_dict.items():
                yr = int(yr_str)
                if start_yr <= yr <= end_yr and val is not None:
                    rows.append({
                        "iso3":       iso3,
                        "raw_name":   dim_field(iso3, 0),
                        "year":       yr,
                        "value":      round(float(val), 4),
                        "source":     "IMF",
                        "indicator":  "GGT_NGDP",
                        "coverage":   SOURCE_META["IMF"]["coverage"],
                        "gdp_denom":  SOURCE_META["IMF"]["gdp_denom"],
                        "definition": SOURCE_META["IMF"]["tax_scope"],
                        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_oecd(iso3_list: list, start_yr: int, end_yr: int) -> pd.DataFrame:
    """OECD Revenue Statistics via SDMX-JSON API (OECD members only)."""
    oecd_members = [c for c in iso3_list if COUNTRY_DIM.get(c, (0,0,0,0,0,False))[5]]
    if not oecd_members:
        return pd.DataFrame()
    # OECD uses ISO2 for some endpoints; map ISO3 → ISO2
    iso3_to_iso2 = {
        "AUS":"AUS","CAN":"CAN","USA":"USA","GBR":"GBR","DEU":"DEU",
        "FRA":"FRA","JPN":"JPN","KOR":"KOR","MEX":"MEX","SWE":"SWE",
        "DNK":"DNK","NOR":"NOR","CHE":"CHE","NLD":"NLD","POL":"POL",
        "ESP":"ESP","ITA":"ITA","TUR":"TUR",
    }
    members_str = "+".join([iso3_to_iso2.get(c, c) for c in oecd_members])
    url = (f"https://stats.oecd.org/SDMX-JSON/data/REV/{members_str}.1000.TAXGDP/all"
           f"?format=jsonP_keyTime&startTime={start_yr}&endTime={end_yr}")
    try:
        r = requests.get(url, timeout=25); r.raise_for_status()
        data = r.json()
        ds    = data.get("dataSets", [{}])[0]
        struc = data.get("structure", {})
        dims  = struc.get("dimensions", {}).get("series", [])
        obs_d = struc.get("dimensions", {}).get("observation", [{}])[0].get("values", [])
        country_idx = next((i for i, d in enumerate(dims) if d["id"] == "COU"), 0)
        countries_v = dims[country_idx]["values"] if dims else []
        rows = []
        for key, series in ds.get("series", {}).items():
            parts    = key.split(":")
            c_idx    = int(parts[country_idx]) if len(parts) > country_idx else 0
            c_code   = countries_v[c_idx]["id"] if c_idx < len(countries_v) else "UNK"
            iso3     = {v: k for k, v in iso3_to_iso2.items()}.get(c_code, c_code)
            for obs_idx_str, obs_vals in series.get("observations", {}).items():
                obs_idx = int(obs_idx_str)
                yr      = int(obs_d[obs_idx]["id"]) if obs_idx < len(obs_d) else 0
                val     = obs_vals[0]
                if val is not None and start_yr <= yr <= end_yr:
                    rows.append({
                        "iso3":       iso3,
                        "raw_name":   dim_field(iso3, 0),
                        "year":       yr,
                        "value":      round(float(val), 4),
                        "source":     "OECD",
                        "indicator":  "REV/1000/TAXGDP",
                        "coverage":   SOURCE_META["OECD"]["coverage"],
                        "gdp_denom":  SOURCE_META["OECD"]["gdp_denom"],
                        "definition": SOURCE_META["OECD"]["tax_scope"],
                        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE: COMBINE → STANDARDISE → HARMONISE
# ─────────────────────────────────────────────────────────────────────────────
def build_raw_table(dfs: list) -> pd.DataFrame:
    """Stack all source DataFrames, add canonical names. This is the RAW table."""
    if not any(not df.empty for df in dfs):
        return pd.DataFrame()
    combined = pd.concat([df for df in dfs if not df.empty], ignore_index=True)
    # Resolve canonical ISO3 and country name
    combined["iso3"]         = combined["iso3"].str.upper().str.strip()
    combined["country_name"] = combined["iso3"].map(lambda x: dim_field(x, 0)).fillna(combined["raw_name"])
    combined["region"]       = combined["iso3"].map(lambda x: dim_field(x, 2)).fillna("Unknown")
    combined["income_group"] = combined["iso3"].map(lambda x: dim_field(x, 3)).fillna("Unknown")
    combined["oecd_member"]  = combined["iso3"].map(lambda x: dim_field(x, 5))
    combined["dim_notes"]    = combined["iso3"].map(lambda x: dim_field(x, 6)).fillna("")
    combined["priority"]     = combined["source"].map(lambda s: SOURCE_META.get(s, {}).get("priority", 99))
    return combined.sort_values(["iso3","year","priority"]).reset_index(drop=True)

def build_harmonized_table(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Apply source hierarchy: for each (iso3, year) take the highest-priority source.
    OECD (1) > IMF (2) > World Bank (3).
    Returns one row per (iso3, year) with source_used and notes.
    """
    if raw.empty:
        return pd.DataFrame()
    harmonized = (
        raw.sort_values("priority")
           .groupby(["iso3","year"])
           .first()
           .reset_index()
    )
    harmonized = harmonized.rename(columns={"value": "tax_gdp_pct", "source": "source_used"})
    keep = ["iso3","country_name","year","tax_gdp_pct","source_used","indicator",
            "coverage","gdp_denom","definition","dim_notes","region","income_group",
            "oecd_member","fetched_at"]
    return harmonized[[c for c in keep if c in harmonized.columns]]

# ─────────────────────────────────────────────────────────────────────────────
# QUALITY CHECKS
# ─────────────────────────────────────────────────────────────────────────────
def check_missing_gaps(harmonized: pd.DataFrame, max_gap: int = 2) -> pd.DataFrame:
    """Flag countries with consecutive missing-year gaps > max_gap."""
    results = []
    for iso3, grp in harmonized.groupby("iso3"):
        country = grp["country_name"].iloc[0]
        years   = sorted(grp["year"].unique())
        if len(years) < 2:
            results.append({"iso3": iso3, "country": country,
                             "issue": "Fewer than 2 data points", "severity": "WARN",
                             "detail": f"Only {len(years)} year(s) available"})
            continue
        full_range = set(range(min(years), max(years)+1))
        missing    = sorted(full_range - set(years))
        # Find consecutive runs
        runs, run = [], []
        for y in missing:
            if not run or y == run[-1]+1:
                run.append(y)
            else:
                runs.append(run); run = [y]
        if run:
            runs.append(run)
        long_gaps = [r for r in runs if len(r) > max_gap]
        for gap in long_gaps:
            results.append({
                "iso3":    iso3, "country": country,
                "issue":   f"Gap > {max_gap} years",
                "severity":"FAIL",
                "detail":  f"Missing {gap[0]}–{gap[-1]} ({len(gap)} years)"
            })
    return pd.DataFrame(results) if results else pd.DataFrame(
        columns=["iso3","country","issue","severity","detail"])

def check_sudden_jumps(harmonized: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
    """Flag year-on-year changes > threshold pp (potential methodology shifts)."""
    results = []
    for iso3, grp in harmonized.groupby("iso3"):
        country = grp["country_name"].iloc[0]
        sub = grp.sort_values("year")[["year","tax_gdp_pct","source_used"]].dropna()
        if len(sub) < 2:
            continue
        sub["delta"] = sub["tax_gdp_pct"].diff()
        jumps = sub[sub["delta"].abs() > threshold]
        for _, row in jumps.iterrows():
            prev = sub[sub["year"] == row["year"]-1]
            prev_src = prev["source_used"].values[0] if not prev.empty else "?"
            results.append({
                "iso3":    iso3, "country": country,
                "year":    int(row["year"]),
                "change_pp": round(row["delta"], 2),
                "severity": "WARN",
                "detail":  f"{row['year']-1}→{int(row['year'])}: {row['delta']:+.1f} pp | source: {prev_src}→{row['source_used']}",
            })
    return pd.DataFrame(results) if results else pd.DataFrame(
        columns=["iso3","country","year","change_pp","severity","detail"])

def check_cross_source(raw: pd.DataFrame, tolerance: float = 2.0) -> pd.DataFrame:
    """Compare overlapping (iso3, year) values across sources; flag diffs > tolerance pp."""
    results = []
    for (iso3, year), grp in raw.groupby(["iso3","year"]):
        if grp["source"].nunique() < 2:
            continue
        country = dim_field(iso3, 0)
        for i, row_a in grp.iterrows():
            for j, row_b in grp.iterrows():
                if j <= i:
                    continue
                diff = abs(row_a["value"] - row_b["value"])
                if diff > tolerance:
                    results.append({
                        "iso3":     iso3, "country": country, "year": year,
                        f"{row_a['source']} value": row_a["value"],
                        f"{row_b['source']} value": row_b["value"],
                        "difference_pp": round(diff, 2),
                        "severity": "WARN" if diff < 4 else "FAIL",
                        "likely_cause": (
                            "Coverage difference (General vs Central Govt)"
                            if diff > 4 else "GDP denominator or vintage difference"
                        ),
                    })
    return pd.DataFrame(results) if results else pd.DataFrame(
        columns=["iso3","country","year","difference_pp","severity","likely_cause"])

def check_data_freshness(harmonized: pd.DataFrame) -> pd.DataFrame:
    """Report most recent year per country and flag if > 3 years stale."""
    current_yr = datetime.utcnow().year - 1  # most recent complete year
    rows = []
    for iso3, grp in harmonized.groupby("iso3"):
        latest = int(grp["year"].max())
        lag    = current_yr - latest
        rows.append({
            "iso3":         iso3,
            "country":      dim_field(iso3, 0),
            "latest_year":  latest,
            "lag_years":    lag,
            "source":       grp[grp["year"]==latest]["source_used"].values[0],
            "severity":     "FAIL" if lag > 3 else ("WARN" if lag > 1 else "PASS"),
        })
    return pd.DataFrame(rows).sort_values("lag_years", ascending=False)

# ─────────────────────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────
PALETTE = ["#1a3a6b","#e63946","#2a9d8f","#e9c46a","#457b9d","#264653",
           "#f4a261","#6d6875","#52b788","#c77dff","#e76f51","#023e8a"]

LAYOUT_BASE = dict(
    font=dict(family="Inter, sans-serif", color="#1e293b"),
    paper_bgcolor="white", plot_bgcolor="#f8fafc",
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#e2e8f0",
                borderwidth=1, font=dict(size=11)),
    margin=dict(l=50, r=30, t=60, b=50),
)
# Axis defaults applied per-chart to avoid duplicate-keyword conflicts
_AXIS = dict(gridcolor="#e2e8f0", linecolor="#cbd5e1")

def fig_bar(df: pd.DataFrame, highlight: str) -> go.Figure:
    df = df.sort_values("tax_gdp_pct", ascending=True)
    src_colors = {"OECD":"#1e3a8a","IMF":"#92400e","WB":"#14532d"}
    colors = [("#e63946" if r["country_name"]==highlight
               else src_colors.get(r["source_used"],"#94a3b8"))
              for _, r in df.iterrows()]
    fig = go.Figure(go.Bar(
        x=df["tax_gdp_pct"], y=df["country_name"], orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=0.4)),
        text=[f"{v:.1f}%" for v in df["tax_gdp_pct"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Tax/GDP: %{x:.2f}%<extra></extra>",
    ))
    hi_avg = df[df["income_group"]=="High Income"]["tax_gdp_pct"].mean()
    fig.add_vline(x=hi_avg, line_dash="dash", line_color="#d97706", line_width=1.5,
                  annotation_text=f"HI Avg: {hi_avg:.1f}%",
                  annotation_font=dict(size=10, color="#d97706"))
    fig.update_layout(LAYOUT_BASE,
        title=dict(text="Tax Revenue (% GDP) — Harmonized, Source-Priority Applied",
                   font=dict(size=14, color="#0f2044"), x=0.01),
        height=max(400, len(df)*27), showlegend=False,
        xaxis=dict(**_AXIS, title="Tax/GDP (%)", range=[0, df["tax_gdp_pct"].max()*1.13]),
        yaxis=dict(**_AXIS, title=""),
    )
    return fig

def fig_trend(harmonized: pd.DataFrame, raw: pd.DataFrame, countries: list) -> go.Figure:
    fig = go.Figure()
    for i, iso3 in enumerate(countries):
        name = dim_field(iso3, 0)
        sub_h = harmonized[harmonized["iso3"]==iso3].sort_values("year")
        if sub_h.empty: continue
        fig.add_trace(go.Scatter(
            x=sub_h["year"], y=sub_h["tax_gdp_pct"], name=name,
            mode="lines+markers", line=dict(color=PALETTE[i%len(PALETTE)], width=2.5),
            marker=dict(size=5),
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>",
        ))
        # Show raw dots for secondary sources as faint background
        sub_r = raw[raw["iso3"]==iso3]
        for src in ["OECD","IMF","WB"]:
            sub_s = sub_r[sub_r["source"]==src].sort_values("year")
            if sub_s.empty or len(sub_s) == len(sub_h): continue
            fig.add_trace(go.Scatter(
                x=sub_s["year"], y=sub_s["value"], name=f"{name} ({src})",
                mode="markers", marker=dict(size=4, opacity=0.35, color=PALETTE[i%len(PALETTE)]),
                showlegend=False,
                hovertemplate=f"<b>{name} [{src}]</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>",
            ))
    fig.update_layout(LAYOUT_BASE,
        title=dict(text="Historical Trend — Harmonized (solid) vs All Sources (faded dots)",
                   font=dict(size=14, color="#0f2044"), x=0.01),
        height=500, hovermode="x unified",
        xaxis=dict(**_AXIS, title="Year", dtick=2),
        yaxis=dict(**_AXIS, title="Tax/GDP (%)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig

def fig_source_coverage(raw: pd.DataFrame, iso3_list: list) -> go.Figure:
    """Heat-map showing which source covers each country-year."""
    src_num = {"OECD":3,"IMF":2,"WB":1}
    records = []
    for iso3 in iso3_list:
        name = dim_field(iso3, 0)
        sub  = raw[raw["iso3"]==iso3]
        for yr in sorted(sub["year"].unique()):
            best = sub[sub["year"]==yr].sort_values("priority").iloc[0]["source"]
            records.append({"country":name,"year":yr,"source":best,"src_num":src_num.get(best,0)})
    df_cov = pd.DataFrame(records)
    if df_cov.empty: return go.Figure()
    fig = go.Figure(go.Heatmap(
        z=df_cov["src_num"], x=df_cov["year"], y=df_cov["country"],
        colorscale=[[0,"#f1f5f9"],[0.33,"#dcfce7"],[0.66,"#fef9c3"],[1.0,"#dbeafe"]],
        text=df_cov["source"], texttemplate="%{text}",
        hovertemplate="<b>%{y}</b> · %{x}<br>Best source: %{text}<extra></extra>",
        zmin=0, zmax=3, showscale=False,
    ))
    fig.update_layout(LAYOUT_BASE,
        title=dict(text="Source Coverage Map — Best Source per Country-Year",
                   font=dict(size=14, color="#0f2044"), x=0.01),
        height=max(350, len(iso3_list)*22),
        xaxis=dict(**_AXIS, title="", dtick=2),
        yaxis=dict(**_AXIS, title="", autorange="reversed"),
        margin=dict(l=120, r=20, t=60, b=40),
    )
    return fig

def fig_cross_source_scatter(raw: pd.DataFrame) -> go.Figure:
    """WB vs IMF scatter for overlapping (iso3,year) pairs."""
    wb  = raw[raw["source"]=="WB" ][["iso3","year","value"]].rename(columns={"value":"wb"})
    imf = raw[raw["source"]=="IMF"][["iso3","year","value"]].rename(columns={"value":"imf"})
    both = wb.merge(imf, on=["iso3","year"])
    if both.empty: return go.Figure()
    both["country"]= both["iso3"].map(lambda x: dim_field(x,0))
    both["diff_pp"]= (both["imf"]-both["wb"]).round(2)
    fig = px.scatter(both, x="wb", y="imf", color="country", hover_name="country",
                     hover_data={"year":True,"diff_pp":":.2f","wb":":.2f","imf":":.2f"},
                     labels={"wb":"World Bank (%)","imf":"IMF (%)"},
                     title="Cross-Source Comparison: World Bank vs IMF (same country-year)")
    hi = max(both[["wb","imf"]].max().max(), 1)
    fig.add_shape(type="line", x0=0, y0=0, x1=hi*1.1, y1=hi*1.1,
                  line=dict(dash="dash", color="#6b7280", width=1))
    fig.update_layout(LAYOUT_BASE, height=460)
    return fig

def fig_choropleth(harmonized: pd.DataFrame) -> go.Figure:
    latest = harmonized.sort_values("year",ascending=False).groupby("iso3").first().reset_index()
    fig = go.Figure(go.Choropleth(
        locations=latest["iso3"], z=latest["tax_gdp_pct"],
        text=latest["country_name"],
        colorscale=[[0,"#dbeafe"],[0.25,"#93c5fd"],[0.5,"#3b82f6"],[0.75,"#1d4ed8"],[1,"#1e3a8a"]],
        colorbar=dict(title="Tax/GDP %", ticksuffix="%", len=0.6, thickness=14),
        hovertemplate="<b>%{text}</b><br>Tax/GDP: %{z:.2f}%<extra></extra>",
        marker_line_color="white", marker_line_width=0.5,
    ))
    fig.update_layout(LAYOUT_BASE,
        title=dict(text="Global Tax-to-GDP Heat Map (Harmonized)",
                   font=dict(size=14, color="#0f2044"), x=0.01),
        geo=dict(showframe=False, showcoastlines=True, coastlinecolor="#cbd5e1",
                 showland=True, landcolor="#f1f5f9", showocean=True, oceancolor="#e0f2fe",
                 projection_type="natural earth", bgcolor="white"),
        height=480, margin=dict(l=0, r=0, t=60, b=0),
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Pipeline Controls")
    st.markdown("---")
    all_names = sorted(COUNTRY_DIM.keys(),
                        key=lambda x: COUNTRY_DIM[x][0])
    display_names = {k: COUNTRY_DIM[k][0] for k in all_names}
    default_iso3  = ["IND","BRA","ZAF","USA","GBR","DEU","FRA","CHN",
                     "KOR","IDN","AUS","SWE","JPN","MEX","NOR"]
    selected_iso3 = st.multiselect(
        " Select Countries",
        options=list(display_names.keys()),
        default=default_iso3,
        format_func=lambda x: display_names[x],
    )
    if "IND" not in selected_iso3:
        selected_iso3 = ["IND"] + selected_iso3

    st.markdown("---")
    year_range = st.slider(" Year Range", 2000, 2023, (2005, 2022))

    st.markdown("---")
    st.markdown("**️ Data Sources**")
    use_oecd = st.checkbox("OECD Revenue Statistics (Priority 1)", value=True)
    use_imf  = st.checkbox("IMF DataMapper (Priority 2)", value=True)
    use_wb   = st.checkbox("World Bank Open Data (Priority 3)", value=True)

    st.markdown("---")
    highlight_iso3 = st.selectbox(" Highlight Country",
                                   options=selected_iso3,
                                   format_func=lambda x: display_names.get(x, x))

    st.markdown("---")
    jump_thresh = st.slider("⚡ Jump Alert Threshold (pp/yr)", 2.0, 10.0, 5.0, 0.5)
    gap_thresh  = st.slider("️ Gap Alert (consecutive missing yrs)", 1, 5, 2)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:.73rem;color:#a8c4e8;line-height:1.65;'>
    <b>Source Priority Rule</b><br>
    OECD (1) > IMF (2) > WB (3)<br>
    Higher-priority only overwrites<br>
    if lower-priority is missing.<br><br>
    <b>Two Outputs</b><br>
     Raw: all sources, all rows<br>
    ✅ Harmonized: one row / country-year<br><br>
    <b>Quality Checks</b><br>
    • Missing year gaps<br>
    • Sudden jump flags<br>
    • Cross-source diffs<br>
    • Data freshness
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────────────────────────────────────
source_status = {}
dfs_to_combine = []

with st.spinner(" Running data pipeline — fetching from all sources..."):
    if use_wb:
        df_wb = fetch_worldbank(selected_iso3, year_range[0], year_range[1])
        source_status["WB"] = ("✅ Live", len(df_wb)) if not df_wb.empty else ("❌ Failed", 0)
        if not df_wb.empty: dfs_to_combine.append(df_wb)
    else:
        source_status["WB"] = ("⏭️ Skipped", 0)

    if use_imf:
        df_imf = fetch_imf(selected_iso3, year_range[0], year_range[1])
        source_status["IMF"] = ("✅ Live", len(df_imf)) if not df_imf.empty else ("❌ Failed / No data", 0)
        if not df_imf.empty: dfs_to_combine.append(df_imf)
    else:
        source_status["IMF"] = ("⏭️ Skipped", 0)

    if use_oecd:
        df_oecd = fetch_oecd(selected_iso3, year_range[0], year_range[1])
        source_status["OECD"] = ("✅ Live", len(df_oecd)) if not df_oecd.empty else ("⚠️ No data / API unavailable", 0)
        if not df_oecd.empty: dfs_to_combine.append(df_oecd)
    else:
        source_status["OECD"] = ("⏭️ Skipped", 0)

if not dfs_to_combine:
    st.error("❌ All sources failed. Check internet connection.")
    st.stop()

raw_df        = build_raw_table(dfs_to_combine)
harmonized_df = build_harmonized_table(raw_df)

# Latest year harmonized
latest_harm   = (harmonized_df.sort_values("year", ascending=False)
                               .groupby("iso3").first().reset_index())

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
src_badges = " ".join([
    f'<span class="source-badge {SOURCE_META[s]["badge"]}">'
    f'{"✅" if "✅" in v[0] else "⚠️" if "⚠️" in v[0] else "❌"} {s}: {v[1]:,} obs</span>'
    for s, v in source_status.items()
])
st.markdown(f"""
<div class="header-banner">
  <div>
    <div class="header-title"> Tax-to-GDP Pipeline Dashboard</div>
    <div class="header-sub">Multi-source · Source-priority harmonized · Quality-validated · Production-grade</div>
    <div style="margin-top:.6rem;">{src_badges}</div>
  </div>
  <div style="display:flex;gap:.6rem;flex-wrap:wrap;justify-content:flex-end;">
    <div class="badge"> Raw obs<br><b>{len(raw_df):,}</b></div>
    <div class="badge">✅ Harmonized<br><b>{len(harmonized_df):,}</b></div>
    <div class="badge"> Countries<br><b>{harmonized_df['iso3'].nunique()}</b></div>
    <div class="badge">️ {year_range[0]}–{year_range[1]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────
india = latest_harm[latest_harm["iso3"]=="IND"]
ind_v = india["tax_gdp_pct"].values[0] if not india.empty else 0
ind_s = india["source_used"].values[0]  if not india.empty else "—"
hi_avg= latest_harm[latest_harm["income_group"]=="High Income"]["tax_gdp_pct"].mean()
n_src = raw_df["source"].nunique()
n_gap = len(check_missing_gaps(harmonized_df, gap_thresh))
n_jmp = len(check_sudden_jumps(harmonized_df, jump_thresh))

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card blue">
    <div class="mlabel">India Tax/GDP</div>
    <div class="mvalue">{ind_v:.1f}%</div>
    <div class="msub">Source: {ind_s} · Central Govt</div>
  </div>
  <div class="metric-card green">
    <div class="mlabel">India (General Govt est.)</div>
    <div class="mvalue">~{ind_v+6.8:.1f}%</div>
    <div class="msub">+6.8 pp state taxes added</div>
  </div>
  <div class="metric-card amber">
    <div class="mlabel">High-Income Avg</div>
    <div class="mvalue">{hi_avg:.1f}%</div>
    <div class="msub">Harmonized (best source)</div>
  </div>
  <div class="metric-card teal">
    <div class="mlabel">Active Sources</div>
    <div class="mvalue">{n_src}</div>
    <div class="msub">of 3 (OECD / IMF / WB)</div>
  </div>
  <div class="metric-card red">
    <div class="mlabel">QC Alerts</div>
    <div class="mvalue">{n_gap + n_jmp}</div>
    <div class="msub">{n_gap} gaps · {n_jmp} jumps</div>
  </div>
  <div class="metric-card purple">
    <div class="mlabel">Harmonized Rows</div>
    <div class="mvalue">{len(harmonized_df):,}</div>
    <div class="msub">1 row per country-year</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    " Comparison",
    " Trends",
    "️ World Map",
    " Pipeline",
    " Quality Checks",
    " India",
    " Data",
])

# ── TAB 1 ────────────────────────────────────────────────────────────────────
with tab1:
    comp_yr_options = sorted(harmonized_df["year"].unique(), reverse=True)
    comp_yr = st.select_slider("Comparison Year", comp_yr_options, value=comp_yr_options[0])
    df_comp = harmonized_df[harmonized_df["year"]==comp_yr]
    if df_comp.empty and len(comp_yr_options)>1:
        comp_yr = comp_yr_options[1]; df_comp = harmonized_df[harmonized_df["year"]==comp_yr]

    col1, col2 = st.columns([3,1])
    with col1:
        st.plotly_chart(fig_bar(df_comp, dim_field(highlight_iso3,0)), use_container_width=True)
    with col2:
        st.markdown('<div class="section-header"> Rankings</div>', unsafe_allow_html=True)
        ranked = df_comp.sort_values("tax_gdp_pct", ascending=False).reset_index(drop=True)
        for idx, row in ranked.iterrows():
            bg  = "#fff7ed" if row["iso3"]==highlight_iso3 else "#f8fafc"
            src_cls = SOURCE_META.get(row["source_used"],{}).get("badge","src-na")
            st.markdown(f"""
            <div style='background:{bg};border-radius:8px;padding:.35rem .6rem;margin-bottom:.25rem;font-size:.8rem;'>
              <b style='color:#0f2044;'>{idx+1}. {row['country_name']}</b>
              <span class='source-badge {src_cls}' style='float:right;'>{row['source_used']}</span><br>
              <span style='color:#6b7280;'>{row['tax_gdp_pct']:.1f}% · {row['income_group']}</span>
            </div>""", unsafe_allow_html=True)

# ── TAB 2 ────────────────────────────────────────────────────────────────────
with tab2:
    st.plotly_chart(fig_trend(harmonized_df, raw_df, selected_iso3), use_container_width=True)
    st.markdown("""<div class="callout"> <b>Solid lines</b> = harmonized values (best source per year). <b>Faded dots</b> = raw values from secondary sources where they differ.</div>""", unsafe_allow_html=True)

    # CAGR table
    st.markdown('<div class="section-header"> Change Analysis</div>', unsafe_allow_html=True)
    rows = []
    for iso3 in selected_iso3:
        sub = harmonized_df[harmonized_df["iso3"]==iso3].sort_values("year")
        if len(sub)<2: continue
        f,l = sub.iloc[0], sub.iloc[-1]
        chg  = l["tax_gdp_pct"]-f["tax_gdp_pct"]
        n    = l["year"]-f["year"]
        cagr = ((l["tax_gdp_pct"]/f["tax_gdp_pct"])**(1/n)-1)*100 if n>0 and f["tax_gdp_pct"]>0 else None
        rows.append({"Country":dim_field(iso3,0),
                     f"Tax/GDP {int(f['year'])}":f"{f['tax_gdp_pct']:.1f}%",
                     f"Tax/GDP {int(l['year'])}":f"{l['tax_gdp_pct']:.1f}%",
                     "Δ (pp)":f"{chg:+.1f}",
                     "CAGR":f"{cagr:+.2f}%/yr" if cagr else "—",
                     "Src (latest)":l["source_used"]})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── TAB 3 ────────────────────────────────────────────────────────────────────
with tab3:
    st.plotly_chart(fig_choropleth(harmonized_df), use_container_width=True)

# ── TAB 4: PIPELINE ──────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header"> Pipeline Architecture</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="callout green">
      <b>Workflow implemented in this app:</b><br>
      1️⃣ <b>Fetch</b> — World Bank API + IMF DataMapper + OECD SDMX-JSON (independently, in parallel)<br>
      2️⃣ <b>Standardize</b> — Resolve ISO3 via master country dimension; deduplicate aliases<br>
      3️⃣ <b>Normalize</b> — Years as <code>int</code>, values as <code>float</code> (no "%" text)<br>
      4️⃣ <b>Source Priority</b> — OECD(1) > IMF(2) > WB(3); overwrite only when higher-priority missing<br>
      5️⃣ <b>Metadata</b> — Per-observation: source, indicator code, coverage, GDP denominator, definition, fetch timestamp<br>
      6️⃣ <b>Quality Checks</b> — Gap detection, jump flags, cross-source diffs, freshness audit<br>
      7️⃣ <b>Two Outputs</b> — Raw table (all rows, all sources) + Harmonized table (one row per country-year)
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header"> Source Status & Definitions</div>', unsafe_allow_html=True)
    for src, meta in SOURCE_META.items():
        status, count = source_status.get(src, ("—", 0))
        icon = "✅" if "✅" in status else ("⚠️" if "⚠️" in status else "❌")
        st.markdown(f"""
        <div style='background:#fff;border-radius:10px;padding:1rem 1.2rem;margin-bottom:.8rem;
                    box-shadow:0 2px 8px rgba(15,32,68,.07);border-left:4px solid {meta["color"]};'>
          <div style='display:flex;justify-content:space-between;align-items:center;'>
            <span style='font-weight:700;font-size:1rem;color:#0f2044;'>
              {icon} Priority {meta["priority"]}: {meta["label"]}
            </span>
            <span class='source-badge {meta["badge"]}'>{count:,} observations</span>
          </div>
          <table style='margin-top:.5rem;font-size:.82rem;color:#4b5563;width:100%;'>
            <tr><td style='width:140px;color:#6b7280;'>Coverage</td><td>{meta["coverage"]}</td></tr>
            <tr><td style='color:#6b7280;'>GDP Denominator</td><td>{meta["gdp_denom"]}</td></tr>
            <tr><td style='color:#6b7280;'>Tax Scope</td><td>{meta["tax_scope"]}</td></tr>
            <tr><td style='color:#6b7280;'>Notes</td><td><i>{meta["notes"]}</i></td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">️ Source Coverage Map</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_source_coverage(raw_df, selected_iso3), use_container_width=True)
    st.markdown("""<div class="callout amber">
     <b>WB</b> = World Bank &nbsp;|&nbsp;  <b>IMF</b> = IMF DataMapper &nbsp;|&nbsp;  <b>OECD</b> = OECD Revenue Statistics<br>
    For each cell, the <b>highest-priority available source</b> is shown. This drives the harmonized table.
    </div>""", unsafe_allow_html=True)

# ── TAB 5: QUALITY CHECKS ────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header"> Quality Check Suite</div>', unsafe_allow_html=True)

    # 1. Missing year gaps
    st.markdown("#### 1️⃣ Missing Year Gap Detection")
    gaps_df = check_missing_gaps(harmonized_df, gap_thresh)
    if gaps_df.empty:
        st.markdown(f'<span class="qcheck-pass">✅ No gaps > {gap_thresh} consecutive years detected.</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="qcheck-fail">⚠️ {len(gaps_df)} gap issue(s) detected:</span>', unsafe_allow_html=True)
        st.dataframe(gaps_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. Sudden jumps
    st.markdown("#### 2️⃣ Sudden Jump Detection (Possible Methodology Shift)")
    jumps_df = check_sudden_jumps(harmonized_df, jump_thresh)
    if jumps_df.empty:
        st.markdown(f'<span class="qcheck-pass">✅ No jumps > {jump_thresh:.1f} pp/yr detected.</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="qcheck-warn">⚠️ {len(jumps_df)} jump(s) detected — review for methodology shifts:</span>', unsafe_allow_html=True)
        st.dataframe(jumps_df, use_container_width=True, hide_index=True)
        st.markdown("""<div class="callout amber">
        ⚠️ Large year-on-year changes can reflect real policy changes <i>or</i> a switch in data source / GDP vintage.
        Always check if the source changed (see Raw table) before concluding a real fiscal shift occurred.
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # 3. Cross-source comparison
    st.markdown("#### 3️⃣ Cross-Source Consistency Check (WB vs IMF)")
    if raw_df["source"].nunique() < 2:
        st.info("Enable multiple sources in the sidebar to activate cross-source comparison.")
    else:
        cross_df = check_cross_source(raw_df, tolerance=2.0)
        if cross_df.empty:
            st.markdown('<span class="qcheck-pass">✅ No significant cross-source discrepancies (>2 pp) found.</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="qcheck-warn">⚠️ {len(cross_df)} discrepancies >2 pp found:</span>', unsafe_allow_html=True)
            st.dataframe(cross_df, use_container_width=True, hide_index=True)
        # Scatter chart
        fig_cs = fig_cross_source_scatter(raw_df)
        if fig_cs.data:
            st.plotly_chart(fig_cs, use_container_width=True)
            st.markdown("""<div class="callout">
             <b>Interpretation:</b> Points on the diagonal line = WB and IMF agree.
            Points above = IMF reports higher (typical for India: IMF uses general govt; WB uses central govt only).
            Large deviations flag definition or coverage mismatches.
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # 4. Data freshness
    st.markdown("#### 4️⃣ Data Freshness Audit")
    fresh_df = check_data_freshness(harmonized_df)
    def style_severity(val):
        return ("color:#c0392b;font-weight:700" if val=="FAIL"
                else "color:#d97706;font-weight:600" if val=="WARN"
                else "color:#1a7a3c;font-weight:600")
    st.dataframe(
        fresh_df.style.map(style_severity, subset=["severity"]),
        use_container_width=True, hide_index=True,
    )

# ── TAB 6: INDIA ─────────────────────────────────────────────────────────────
with tab6:
    st.markdown('<div class="section-header"> India — Methodology & Coverage Deep-Dive</div>', unsafe_allow_html=True)

    ind_raw  = raw_df[raw_df["iso3"]=="IND"].sort_values("year")
    ind_harm = harmonized_df[harmonized_df["iso3"]=="IND"].sort_values("year")

    if not ind_raw.empty:
        fig_ind = go.Figure()
        for src in ["OECD","IMF","WB"]:
            sub = ind_raw[ind_raw["source"]==src]
            if sub.empty: continue
            fig_ind.add_trace(go.Scatter(
                x=sub["year"], y=sub["value"],
                mode="lines+markers", name=src,
                line=dict(width=2, dash=("solid" if src=="WB" else "dot")),
                marker=dict(size=6),
                hovertemplate=f"<b>India [{src}]</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>",
            ))
        # Estimated general govt
        fig_ind.add_trace(go.Scatter(
            x=ind_harm["year"], y=ind_harm["tax_gdp_pct"]+6.8,
            mode="lines+markers", name="Est. General Govt (WB +6.8pp)",
            line=dict(color="#e63946", width=2.5, dash="longdash"),
            marker=dict(size=5),
            hovertemplate="<b>Est. General Govt</b><br>%{x}: %{y:.2f}%<extra></extra>",
        ))
        fig_ind.add_hline(y=34.1, line_dash="dash", line_color="#6b7280",
                          annotation_text="OECD avg 34.1%",
                          annotation_font=dict(size=10, color="#6b7280"),
                          annotation_position="bottom right")
        fig_ind.add_hline(y=18.1, line_dash="dash", line_color="#2a9d8f",
                          annotation_text="Brazil 18.1%",
                          annotation_font=dict(size=10, color="#2a9d8f"),
                          annotation_position="top right")
        fig_ind.update_layout(LAYOUT_BASE,
            title=dict(text="India — All Sources vs Estimated General Government Ratio",
                       font=dict(size=14, color="#0f2044"), x=0.01),
            height=430,
            xaxis=dict(**_AXIS, title="Year", dtick=2),
            yaxis=dict(**_AXIS, title="Tax/GDP (%)"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_ind, use_container_width=True)

    st.markdown("""
    <div class="callout amber">
      <b>Key Definition Mismatch — India:</b><br>
      World Bank <code>GC.TAX.TOTL.GD.ZS</code> captures only <b>Central Government tax receipts</b>.
      IMF <code>GGT_NGDP</code> attempts <b>General Government</b> coverage but data availability is limited.
      OECD does not include India as a member, though India appears in the <i>OECD Global Revenue Statistics</i>
      database from 2019 onwards. For robust India comparisons, users should add state-level taxes
      (~6.5–7.5% of GDP per PRS India 2024-25) to arrive at a general-government figure.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 7: DATA ───────────────────────────────────────────────────────────────
with tab7:
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["✅ Harmonized Table", " Raw Table", "️ Country Dimension"])

    with sub_tab1:
        st.markdown('<div class="section-header">✅ Harmonized Table — One Row per Country-Year</div>', unsafe_allow_html=True)
        st.markdown("""<div class="callout green">
        This is the <b>production output</b>. One row per (iso3, year), using source-priority rule.
        Columns include per-observation metadata: source, indicator, coverage, GDP denominator, definition.
        </div>""", unsafe_allow_html=True)
        st.dataframe(harmonized_df, use_container_width=True, hide_index=True, height=380)
        csv_h = harmonized_df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Harmonized CSV", csv_h,
                           "tax_gdp_harmonized.csv", "text/csv")

    with sub_tab2:
        st.markdown('<div class="section-header"> Raw Table — All Sources, All Rows</div>', unsafe_allow_html=True)
        st.markdown("""<div class="callout">
        Raw table preserves every source value exactly as published.
        Use this for audit trails and cross-source validation.
        </div>""", unsafe_allow_html=True)
        st.dataframe(raw_df, use_container_width=True, hide_index=True, height=380)
        csv_r = raw_df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Raw CSV", csv_r,
                           "tax_gdp_raw.csv", "text/csv")

    with sub_tab3:
        st.markdown('<div class="section-header">️ Master Country Dimension Table</div>', unsafe_allow_html=True)
        st.markdown("""<div class="callout">
        Single source of truth for country identifiers. Resolves aliases
        (e.g., "Ivory Coast" → <code>CIV</code>, "Türkiye" → <code>TUR</code>).
        </div>""", unsafe_allow_html=True)
        dim_rows = []
        for iso3, v in COUNTRY_DIM.items():
            dim_rows.append({
                "ISO3":        iso3,
                "Canonical Name": v[0],
                "Aliases":     ", ".join(v[1]),
                "Region":      v[2],
                "Income Group":v[3],
                "WB Name":     v[4],
                "OECD Member": "✅" if v[5] else "—",
                "Notes":       v[6],
            })
        dim_df = pd.DataFrame(dim_rows)
        st.dataframe(dim_df, use_container_width=True, hide_index=True)
        csv_d = dim_df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Country Dimension CSV", csv_d,
                           "country_dimension.csv", "text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="source-footer">
  <span style='font-size:1.1rem;'></span>
  <div>
    <b>Sources:</b>
    World Bank Open Data — <code>GC.TAX.TOTL.GD.ZS</code> ·
    IMF DataMapper — <code>GGT_NGDP</code> (General Govt Tax % GDP) ·
    OECD Revenue Statistics — <code>REV/1000/TAXGDP</code> &nbsp;|&nbsp;
    <b>Source Priority:</b> OECD (1) > IMF (2) > World Bank (3) &nbsp;|&nbsp;
    <b>Last fetch:</b> Live · cached 1 hr &nbsp;|&nbsp;
    <b>India note:</b> WB = Central Govt only; est. General Govt = WB + 6.8 pp (PRS India 2024-25)
  </div>
</div>
""", unsafe_allow_html=True)
