import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(
    page_title="U.S. Consumer Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }
[data-testid="stMetricValue"] { font-family: 'DM Serif Display', serif; font-size: 1.8rem; }
[data-testid="stMetricLabel"] { font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.6; }
div[data-testid="metric-container"] {
    background: #f8f7f4; border: 1px solid #e8e4dc;
    border-radius: 4px; padding: 1rem 1.25rem;
}
section[data-testid="stSidebar"] { background: #0f1117; }
section[data-testid="stSidebar"] * { color: #e8e8e8 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── LOAD ──────────────────────────────────────────────────────────────────────


@st.cache_data
def load():
    df = pd.read_csv("sentiment_clean.csv")
    df["Date"] = pd.to_datetime(df["Time Period"])
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df.dropna(subset=["Value", "Date"])


df = load()

# ── METRIC GROUPS ─────────────────────────────────────────────────────────────

GROUPS = {
    "Consumer Sentiment Indices": {
        "metrics": [
            "Michigan ICS – Overall",
            "OECD CCI – Amplitude Adjusted",
            "OECD CCI – Standardised",
        ],
        "description": "Composite indices measuring how optimistic or pessimistic consumers feel about the economy. Higher = more optimistic. Note: each index uses a different baseline scale, so they are normalized to 0–100 for comparison.",
        "unit_note": "Normalized (different baselines: ICS uses 1966Q1=100; OECD uses long-run avg=100)",
        "normalize": True,
    },
    "Inflation Expectations": {
        "metrics": [
            "Michigan – 1yr Inflation Expectations",
            "Cleveland Fed – 1yr Inflation Expectations",
            "Cleveland Fed – 10yr Inflation Expectations",
            "5yr Breakeven Inflation Rate",
        ],
        "description": "What consumers and markets expect inflation to be over the next 1–10 years. Higher values indicate greater inflation concern, which typically reflects lower consumer confidence in purchasing power.",
        "unit_note": "All in Percent (%)",
        "normalize": False,
    },
    "Investor Confidence": {
        "metrics": [
            "Yale – Individual 1yr Stock Confidence",
            "Yale – Institutional 1yr Stock Confidence",
        ],
        "description": "Percentage of individual and institutional investors who expect the stock market to be higher one year from now. Reflects forward-looking confidence from both retail and professional investors.",
        "unit_note": "Percent (%) of respondents expecting market to rise",
        "normalize": False,
    },
}

COLORS = {
    "Michigan ICS – Overall": "#1a1a2e",
    "OECD CCI – Amplitude Adjusted": "#e63946",
    "OECD CCI – Standardised": "#457b9d",
    "Michigan – 1yr Inflation Expectations": "#f4a261",
    "Cleveland Fed – 1yr Inflation Expectations": "#2a9d8f",
    "Cleveland Fed – 10yr Inflation Expectations": "#e9c46a",
    "5yr Breakeven Inflation Rate": "#264653",
    "Yale – Individual 1yr Stock Confidence": "#6d6875",
    "Yale – Institutional 1yr Stock Confidence": "#b5838d",
}

DESCRIPTIONS = {
    "Michigan ICS – Overall": "University of Michigan Index of Consumer Sentiment. Measures consumer attitudes on personal finance, business conditions, and buying conditions. Base: 1966 Q1 = 100.",
    "OECD CCI – Amplitude Adjusted": "OECD Consumer Confidence Indicator, amplitude-adjusted. Values above 100 indicate optimism above the long-run average; below 100 indicates pessimism.",
    "OECD CCI – Standardised": "OECD Consumer Confidence Indicator, standardised version. Tracks deviation from long-run average in standard deviation units, rescaled.",
    "Michigan – 1yr Inflation Expectations": "Median expected inflation rate over the next 12 months, from the University of Michigan Surveys of Consumers.",
    "Cleveland Fed – 1yr Inflation Expectations": "Cleveland Fed model-based estimate of expected inflation over the next year, derived from Treasury yields and inflation swaps.",
    "Cleveland Fed – 10yr Inflation Expectations": "Cleveland Fed model-based estimate of expected inflation over the next 10 years. A long-run anchor for inflation credibility.",
    "5yr Breakeven Inflation Rate": "Market-implied inflation expectation over 5 years, derived from the spread between nominal and inflation-protected Treasury yields (TIPS).",
    "Yale – Individual 1yr Stock Confidence": "% of individual investors who expect the Dow Jones to be higher one year from now. Yale School of Management Survey.",
    "Yale – Institutional 1yr Stock Confidence": "% of institutional investors who expect the Dow Jones to be higher one year from now. Yale School of Management Survey.",
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Controls")
    st.markdown("---")
    min_yr = int(df["Date"].dt.year.min())
    max_yr = int(df["Date"].dt.year.max())
    year_range = st.slider("Date Range", min_yr, max_yr, (1990, max_yr))
    st.markdown("---")
    st.markdown("**Show Groups**")
    selected_groups = []
    for g in GROUPS:
        if st.checkbox(g, value=True):
            selected_groups.append(g)

# ── HEADER ────────────────────────────────────────────────────────────────────

st.markdown("# U.S. Consumer Sentiment Dashboard")
st.markdown(
    "This dashboard tracks key measures of U.S. consumer sentiment, inflation expectations, "
    "and investor confidence using data from FRED, University of Michigan, OECD, "
    "Cleveland Fed, and Yale ICF."
)
st.markdown("---")

# ── KPI CARDS ─────────────────────────────────────────────────────────────────

kpi_metrics = [
    ("Michigan ICS – Overall", "Latest ICS"),
    ("OECD CCI – Standardised", "OECD CCI"),
    ("Michigan – 1yr Inflation Expectations", "1yr Inflation Exp."),
    ("Yale – Individual 1yr Stock Confidence", "Yale Individual"),
]

mask_all = (df["Date"].dt.year >= year_range[0]) & (df["Date"].dt.year <= year_range[1])
filtered_all = df[mask_all]

kpi_cols = st.columns(4)
for i, (metric, label) in enumerate(kpi_metrics):
    mdata = filtered_all[filtered_all["Metric Name"] == metric].sort_values("Date")
    if len(mdata) < 1:
        continue
    latest = mdata.iloc[-1]
    prev = mdata.iloc[-2] if len(mdata) > 1 else None
    delta = round(latest["Value"] - prev["Value"], 2) if prev is not None else None
    unit = latest["Unit"]
    kpi_cols[i].metric(
        label=f"{label} · {latest['Time Period']}",
        value=f"{latest['Value']:.1f}",
        delta=f"{delta:+.2f}" if delta is not None else None,
        help=DESCRIPTIONS.get(metric, ""),
    )

st.markdown("---")

# ── THREE SEPARATE CHARTS ─────────────────────────────────────────────────────

for group_name in selected_groups:
    group = GROUPS[group_name]
    metrics = group["metrics"]
    normalize = group["normalize"]
    description = group["description"]
    unit_note = group["unit_note"]

    st.markdown(f"### {group_name}")
    st.caption(description)

    # Filter data for this group
    mask = (
        (df["Date"].dt.year >= year_range[0])
        & (df["Date"].dt.year <= year_range[1])
        & (df["Metric Name"].isin(metrics))
    )
    gdf = df[mask].copy()

    if gdf.empty:
        st.info("No data available for this date range.")
        st.markdown("---")
        continue

    # Normalize if needed
    if normalize:

        def norm(s):
            mn, mx = s.min(), s.max()
            return (s - mn) / (mx - mn) * 100 if mx != mn else s * 0 + 50

        gdf["PlotValue"] = gdf.groupby("Metric Name")["Value"].transform(norm)
        yaxis_title = "Normalized (0 = historical low, 100 = historical high)"
    else:
        gdf["PlotValue"] = gdf["Value"]
        yaxis_title = unit_note

    # Build chart
    fig = go.Figure()
    for metric in metrics:
        mdata = gdf[gdf["Metric Name"] == metric].sort_values("Date")
        if mdata.empty:
            continue
        short = (
            metric.split("–")[-1].strip()
            if "–" in metric
            else metric.split("–")[0].strip()
        )
        fig.add_trace(
            go.Scatter(
                x=mdata["Date"],
                y=mdata["PlotValue"],
                name=short,
                mode="lines",
                line=dict(color=COLORS.get(metric, "#888"), width=2),
                hovertemplate=(
                    f"<b>{metric}</b><br>"
                    "Date: %{x|%b %Y}<br>"
                    "Value: %{y:.2f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        height=380,
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="DM Sans"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        xaxis=dict(showgrid=True, gridcolor="#f0ece4", title=None),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f0ece4",
            title=dict(text=yaxis_title, font=dict(size=11)),
        ),
        margin=dict(t=50, b=20, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Indicator legend
    with st.expander("What do these indicators mean?"):
        for metric in metrics:
            mdata = gdf[gdf["Metric Name"] == metric]
            if mdata.empty:
                continue
            latest_val = mdata.sort_values("Date").iloc[-1]["Value"]
            st.markdown(
                f"**{metric}** — Latest: `{latest_val:.2f}` · {unit_note}  \n"
                f"{DESCRIPTIONS.get(metric, '')}"
            )

    st.markdown("---")

# ── CORRELATION ───────────────────────────────────────────────────────────────

with st.expander("📊 Cross-group Correlation Heatmap"):
    st.caption(
        "Shows how different sentiment indicators move together. +1 = always move in same direction, -1 = always move in opposite directions, 0 = no relationship."
    )
    all_metrics = [m for g in selected_groups for m in GROUPS[g]["metrics"]]
    mask2 = (
        (df["Date"].dt.year >= year_range[0])
        & (df["Date"].dt.year <= year_range[1])
        & (df["Metric Name"].isin(all_metrics))
    )
    corr_df = df[mask2].copy()
    pivot = corr_df.pivot_table(index="Date", columns="Metric Name", values="Value")
    pivot = pivot[[c for c in all_metrics if c in pivot.columns]]

    if pivot.shape[1] >= 2:
        corr = pivot.corr()
        short_labels = [
            m.split("–")[-1].strip()[:22] if "–" in m else m[:22] for m in corr.columns
        ]
        fig_c = go.Figure(
            go.Heatmap(
                z=corr.values,
                x=short_labels,
                y=short_labels,
                colorscale=[[0.0, "#e63946"], [0.5, "#f8f7f4"], [1.0, "#1a1a2e"]],
                zmid=0,
                text=[[f"{v:.2f}" for v in row] for row in corr.values],
                texttemplate="%{text}",
                textfont=dict(size=10),
            )
        )
        fig_c.update_layout(
            height=420,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="DM Sans"),
            xaxis=dict(tickfont=dict(size=9), tickangle=-30),
            yaxis=dict(tickfont=dict(size=9)),
            margin=dict(t=20, b=80, l=80, r=20),
        )
        st.plotly_chart(fig_c, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────

st.caption(
    f"SHF-D2  ·  Sources: FRED, University of Michigan, OECD, Cleveland Fed, Yale ICF  ·  "
    f"{year_range[0]}–{year_range[1]}"
)
