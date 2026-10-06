import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from sql_tasks import TASKS

# =========================================================
# THEME (palette, Plotly template, chart helpers, global CSS)
# =========================================================
# ---------------------------------------------------------
# PALETTE
# ---------------------------------------------------------
C = {
    "bg": "#0c1220",
    "surface": "#131c2e",
    "surface_2": "#18233a",
    "border": "#243049",
    "text": "#f1f5f9",
    "muted": "#94a3b8",
    "accent": "#818cf8",     # indigo - primary / close price
    "up": "#2dd4bf",         # teal  - gains / buy
    "down": "#fb7185",       # coral - losses / sell
    "ma20": "#38bdf8",       # sky
    "ma50": "#fbbf24",       # amber
}

# One fixed colour per stock, so a company looks the same on every page
STOCK_COLORS = {
    "Bajaj Auto": "#818cf8",
    "Eicher Motors": "#2dd4bf",
    "Hero Motocorp": "#fbbf24",
    "Infosys": "#38bdf8",
    "TCS": "#f472b6",
    "TVS Motors": "#fb923c",
}

FONT = "Manrope, sans-serif"

# ---------------------------------------------------------
# PLOTLY TEMPLATE
# ---------------------------------------------------------
pio.templates["stock_dark"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, color=C["text"], size=13),
        title=dict(font=dict(size=16, color=C["text"]), x=0.01),
        colorway=[C["accent"], C["ma20"], C["ma50"], C["up"], "#f472b6", "#fb923c"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(148,163,184,.08)", zeroline=False,
                   linecolor=C["border"], tickfont=dict(color=C["muted"])),
        yaxis=dict(gridcolor="rgba(148,163,184,.10)", zeroline=False,
                   linecolor=C["border"], tickfont=dict(color=C["muted"])),
        legend=dict(font=dict(color=C["muted"]), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=C["surface_2"], bordercolor=C["border"],
                        font=dict(family=FONT, color=C["text"])),
    )
)
pio.templates.default = "stock_dark"


def signed_colors(values):
    """Teal for gains, coral for losses - use for bars with +/- values."""
    return [C["up"] if v >= 0 else C["down"] for v in values]


def base_chart(fig, height=450):
    """Same name/signature as before, so existing calls keep working."""
    fig.update_layout(
        template="stock_dark",
        height=height,
        margin=dict(l=10, r=20, t=60, b=20),
        hovermode="x unified",
        bargap=0.35,
    )
    # readable data labels on every trace that shows text
    fig.update_traces(
        textfont=dict(family=FONT, color=C["text"]),
        selector=dict(type="bar"),
    )
    fig.update_traces(
        marker=dict(cornerradius=6),
        selector=dict(type="bar"),
    )
    return fig


# ---------------------------------------------------------
# GLOBAL CSS
# ---------------------------------------------------------
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{ font-family: {FONT}; }}
.stApp {{
    background:
        radial-gradient(900px 400px at 8% -10%, rgba(129,140,248,.14), transparent 60%),
        radial-gradient(700px 360px at 95% 0%, rgba(45,212,191,.08), transparent 60%),
        {C['bg']};
}}
header[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {C['surface']};
    border-right: 1px solid {C['border']};
}}
[data-testid="stSidebar"] * {{ color: {C['text']}; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
    padding: 9px 12px; border-radius: 10px; margin-bottom: 2px;
    transition: background .15s;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: {C['surface_2']}; }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
    background: rgba(129,140,248,.16);
    box-shadow: inset 3px 0 0 {C['accent']};
}}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display: none; }}

/* Headings */
.main-title {{
    font-size: 40px; font-weight: 800; letter-spacing: -1.4px; line-height: 1.1;
    background: linear-gradient(90deg, #f8fafc 30%, {C['accent']});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 6px;
}}
.subtitle {{ color: {C['muted']}; font-size: 15px; margin-bottom: 28px; max-width: 70ch; }}
.section-title {{
    color: {C['text']}; font-size: 20px; font-weight: 700;
    margin: 30px 0 14px; padding-left: 12px;
    border-left: 3px solid {C['accent']};
}}

/* Metric cards */
.metric-card {{
    background: linear-gradient(160deg, {C['surface_2']}, {C['surface']});
    border: 1px solid {C['border']}; border-radius: 16px;
    padding: 20px; min-height: 124px;
    transition: border-color .2s, transform .2s;
}}
.metric-card:hover {{ border-color: {C['accent']}; transform: translateY(-2px); }}
.metric-label {{ color: {C['muted']}; font-size: 13px; font-weight: 600; }}
.metric-value {{
    color: {C['text']}; font-size: 28px; font-weight: 800; margin-top: 8px;
    font-variant-numeric: tabular-nums; letter-spacing: -.5px;
}}
.metric-sub {{ color: {C['muted']}; font-size: 12px; margin-top: 6px; }}

/* Insight / recommendation / status cards */
.insight-card, .recommendation-card, .success-card, .warning-card {{
    border-radius: 14px; padding: 18px 20px; margin-bottom: 12px;
    border: 1px solid {C['border']}; border-left-width: 4px;
}}
.insight-card {{ background: {C['surface']}; border-left-color: {C['accent']}; }}
.recommendation-card {{ background: {C['surface_2']}; border-left-color: {C['ma20']}; }}
.success-card {{ background: rgba(45,212,191,.07); border-color: rgba(45,212,191,.28); border-left-color: {C['up']}; }}
.warning-card {{ background: rgba(251,191,36,.07); border-color: rgba(251,191,36,.28); border-left-color: {C['ma50']}; margin-top: 12px; }}

.insight-title, .recommendation-title {{ color: {C['text']}; font-size: 15px; font-weight: 700; }}
.insight-text, .recommendation-text {{ color: #a9b6c9; font-size: 14px; line-height: 1.6; margin-top: 6px; }}
.success-title {{ color: {C['up']}; font-size: 15px; font-weight: 700; }}
.success-text {{ color: #9fd8cf; font-size: 14px; line-height: 1.6; margin-top: 6px; }}
.warning-title {{ color: {C['ma50']}; font-size: 15px; font-weight: 700; }}
.warning-text {{ color: #d3bf8a; font-size: 14px; line-height: 1.6; margin-top: 6px; }}

/* Streamlit native widgets */
div[data-testid="stMetric"] {{
    background: {C['surface']}; border: 1px solid {C['border']};
    border-radius: 14px; padding: 15px;
}}
div[data-baseweb="select"] > div, .stTextArea textarea {{
    background: {C['surface']} !important; border-color: {C['border']} !important;
    border-radius: 10px !important;
}}
.stTextArea textarea {{ font-size: 14px; }}
.stButton button[kind="primary"] {{
    background: {C['accent']}; border: none; border-radius: 10px;
    color: #0c1220; font-weight: 700;
}}
.stButton button[kind="primary"]:hover {{ filter: brightness(1.1); }}
.stDownloadButton button {{
    width: 100%; background: {C['surface_2']}; border: 1px solid {C['border']};
    border-radius: 10px; color: {C['text']};
}}
.stDownloadButton button:hover {{ border-color: {C['accent']}; color: {C['accent']}; }}
[data-testid="stDataFrame"] {{ border: 1px solid {C['border']}; border-radius: 12px; overflow: hidden; }}
hr {{ border-color: {C['border']}; }}
</style>
"""


# =========================================================
# CONFIG
# =========================================================
DB = "stock_market.db"

STOCKS = {
    "bajaj_auto": "Bajaj Auto",
    "eicher_motors": "Eicher Motors",
    "hero_motocorp": "Hero Motocorp",
    "infosys": "Infosys",
    "tcs": "TCS",
    "tvs_motors": "TVS Motors",
}

st.set_page_config(page_title="Stock Market Analytics", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# =========================================================
# DATA
# =========================================================
@st.cache_data
def load_data(table):
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def run_sql(sql):
    conn = sqlite3.connect(DB)
    try:
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()


def prepare_stock_data(table):
    df = load_data(table).copy()
    df["ma20"] = df["close_price"].rolling(20).mean()
    df["ma50"] = df["close_price"].rolling(50).mean()
    df["daily_return"] = df["close_price"].pct_change() * 100
    p20, p50 = df["ma20"].shift(1), df["ma50"].shift(1)
    df["signal"] = "Hold"
    df.loc[(p20 <= p50) & (df["ma20"] > df["ma50"]), "signal"] = "Buy"
    df.loc[(p20 >= p50) & (df["ma20"] < df["ma50"]), "signal"] = "Sell"
    return df


def calculate_metrics(table):
    df = prepare_stock_data(table)
    first, last = df["close_price"].iloc[0], df["close_price"].iloc[-1]
    rets = df["daily_return"].dropna()
    drawdown = (df["close_price"] / df["close_price"].cummax() - 1) * 100
    latest = df.iloc[-1]

    if pd.notna(latest["ma20"]) and pd.notna(latest["ma50"]):
        trend = ("Bullish" if latest["ma20"] > latest["ma50"]
                 else "Bearish" if latest["ma20"] < latest["ma50"] else "Neutral")
    else:
        trend = "Insufficient Data"

    return {
        "Stock": STOCKS[table],
        "First Price": first,
        "Latest Price": last,
        "Return %": (last - first) / first * 100,
        "Volatility %": rets.std(),
        "Positive Days %": (rets > 0).sum() / len(rets) * 100 if len(rets) else 0,
        "Max Drawdown %": drawdown.min(),
        "Worst Day %": rets.min(),
        "Best Day %": rets.max(),
        "MA20": latest["ma20"],
        "MA50": latest["ma50"],
        "Trend": trend,
        "Buy Signals": (df["signal"] == "Buy").sum(),
        "Sell Signals": (df["signal"] == "Sell").sum(),
        "Hold Sessions": (df["signal"] == "Hold").sum(),
    }


@st.cache_data
def build_comparison():
    return pd.DataFrame([calculate_metrics(t) for t in STOCKS])


# =========================================================
# UI HELPERS
# =========================================================
def html(block):
    st.markdown(block, unsafe_allow_html=True)


def page_header(title, subtitle):
    html(f'<div class="main-title">{title}</div>')
    html(f'<div class="subtitle">{subtitle}</div>')


def section(title):
    html(f'<div class="section-title">{title}</div>')


def metric_card(label, value, sub="", color=None):
    style = f' style="color:{color}"' if color else ""
    html(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value"{style}>{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""")


def _card(kind, title, text):
    html(f"""
    <div class="{kind}-card">
        <div class="{kind}-title">{title}</div>
        <div class="{kind}-text">{text}</div>
    </div>""")


def insight(title, text): _card("insight", title, text)
def recommendation(title, text): _card("recommendation", title, text)
def warning(title, text): _card("warning", title, text)
def success(title, text): _card("success", title, text)


def show(fig, height=450):
    st.plotly_chart(base_chart(fig, height), use_container_width=True)


def hbar(df, x, title, colors, height=450, right_margin=None):
    """Horizontal ranked bar chart with coloured bars and data labels."""
    df = df.sort_values(x, ascending=(x != "Max Drawdown %"))
    fig = px.bar(df, x=x, y="Stock", orientation="h", text=x, title=title)
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside",
                      cliponaxis=False,
                      marker_color=colors(df) if callable(colors) else colors)
    if right_margin:
        fig = base_chart(fig, height)
        fig.update_layout(margin=dict(l=10, r=right_margin, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        show(fig, height)


def money(v):
    return f"₹{v:,.2f}"


def tint(v):
    return C["up"] if v >= 0 else C["down"]


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.markdown("## 📈 Stock Analytics")
st.sidebar.caption("SQL • Python • Streamlit")

page = st.sidebar.radio("Navigation", [
    "Overview", "Stock Analysis", "Cross-Stock Insights",
    "SQL Tasks", "SQL Playground", "Data Explorer",
])

st.sidebar.divider()
st.sidebar.markdown("### Dataset")
for line in ["Period: 2015 – 2018", "Companies: 6", "Records: 5,334", "Database: SQLite"]:
    st.sidebar.caption(line)

# =========================================================
# OVERVIEW
# =========================================================
if page == "Overview":
    page_header("Stock Market Analytics",
                "Business-focused analysis of six Indian stocks using SQL, Python and interactive visual analytics.")

    comparison = build_comparison()
    best = comparison.loc[comparison["Return %"].idxmax()]
    lowest_risk = comparison.loc[comparison["Volatility %"].idxmin()]
    highest_risk = comparison.loc[comparison["Volatility %"].idxmax()]
    bullish = (comparison["Trend"] == "Bullish").sum()
    bearish = (comparison["Trend"] == "Bearish").sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Stocks", "6", "Companies analyzed")
    with c2: metric_card("Best Return", f"{best['Return %']:.2f}%", best["Stock"], C["up"])
    with c3: metric_card("Lowest Volatility", f"{lowest_risk['Volatility %']:.2f}%", lowest_risk["Stock"], C["ma20"])
    with c4: metric_card("Bullish Stocks", str(bullish), f"{bearish} currently bearish", C["accent"])

    section("Executive Summary")
    col1, col2 = st.columns(2)
    with col1:
        insight("🏆 Performance Leader",
                f"{best['Stock']} produced the strongest first-to-last historical return at "
                f"{best['Return %']:.2f}%, making it the top performer in this dataset on a simple price-return basis.")
        insight("🛡️ Lower Historical Volatility",
                f"{lowest_risk['Stock']} recorded the lowest daily-return volatility at "
                f"{lowest_risk['Volatility %']:.2f}%, a comparatively stable price path within this dataset.")
    with col2:
        insight("⚠️ Highest Historical Risk",
                f"{highest_risk['Stock']} had the highest daily-return volatility at "
                f"{highest_risk['Volatility %']:.2f}%. Additional risk monitoring would be appropriate.")
        insight("📊 Market Trend Snapshot",
                f"{bullish} of the 6 stocks currently have MA20 above MA50, while {bearish} have MA20 below MA50. "
                "The moving-average structure gives a simple indication of recent trend direction.")

    section("Performance Ranking")
    hbar(comparison, "Return %", "Historical First-to-Last Return",
         lambda d: signed_colors(d["Return %"]), right_margin=80)

    section("Return vs Historical Risk")
    fig = px.scatter(comparison, x="Volatility %", y="Return %", text="Stock",
                     size="Positive Days %", color="Stock",
                     color_discrete_map=STOCK_COLORS, hover_name="Stock",
                     title="Performance vs Daily Volatility")
    fig.update_traces(textposition="top center", textfont=dict(color=C["text"]))
    fig.update_xaxes(title="Daily Volatility (%)")
    fig.update_yaxes(title="Historical Return (%)")
    fig.update_layout(showlegend=False, hovermode="closest")
    show(fig, 500)

    section("Data-Driven Recommendations")
    recommendation("1. Prioritize Trend Confirmation",
                   "Prefer stocks where MA20 stays above MA50 and avoid treating a single day's move as a signal. "
                   "A moving-average crossover gives more structured trend confirmation.")
    recommendation("2. Balance Return With Volatility",
                   f"{best['Stock']} is the historical performance leader, but return should be judged alongside "
                   f"volatility and drawdown. {lowest_risk['Stock']} has the lowest daily volatility in this dataset.")
    recommendation("3. Monitor Drawdowns",
                   "Stocks with large maximum drawdowns need stronger risk monitoring. Historical returns can hide "
                   "periods of substantial capital decline.")
    recommendation("4. Investigate Extreme Daily Moves",
                   "Large one-day moves should be investigated before drawing conclusions. Corporate actions can "
                   "create artificial jumps or drops in unadjusted data.")
    recommendation("5. Use SQL Signals as a Screening Tool",
                   "The Buy/Sell/Hold crossover logic demonstrates analytical decision rules, but it is a screening "
                   "framework, not a guaranteed trading strategy.")
    warning("⚠️ Decision-Making Caveat",
            "This dashboard uses historical market data and technical indicators. It does not include dividends, "
            "taxes, brokerage costs, macroeconomic conditions, company fundamentals, news or future market conditions. "
            "The recommendations are analytical observations for this dataset, not personalized investment advice.")

# =========================================================
# STOCK ANALYSIS
# =========================================================
elif page == "Stock Analysis":
    page_header("Stock Analysis", "Detailed price, risk, trend and signal analysis.")

    selected = st.selectbox("Select Stock", list(STOCKS.keys()), format_func=lambda x: STOCKS[x])
    name = STOCKS[selected]
    df = prepare_stock_data(selected)
    m = calculate_metrics(selected)

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Latest Close", money(m["Latest Price"]), name)
    with c2: metric_card("Historical Return", f"{m['Return %']:.2f}%", "First → last close", tint(m["Return %"]))
    with c3: metric_card("Daily Volatility", f"{m['Volatility %']:.2f}%", "Historical standard deviation", C["ma20"])
    with c4: metric_card("Max Drawdown", f"{m['Max Drawdown %']:.2f}%", "Peak → trough", C["down"])

    section("Current Trend Assessment")
    trend_color = {"Bullish": C["up"], "Bearish": C["down"]}.get(m["Trend"])
    col1, col2, col3 = st.columns(3)
    with col1: metric_card("Trend", m["Trend"], "MA20 vs MA50", trend_color)
    with col2: metric_card("MA20", money(m["MA20"]), "20-session average", C["ma20"])
    with col3: metric_card("MA50", money(m["MA50"]), "50-session average", C["ma50"])

    if m["Trend"] == "Bullish":
        success("Positive Trend Structure",
                f"{name} currently has MA20 above MA50, indicating a positive recent trend structure.")
    elif m["Trend"] == "Bearish":
        warning("Negative Trend Structure",
                f"{name} currently has MA20 below MA50, indicating weaker recent momentum.")
    else:
        insight("Neutral Trend Structure",
                f"{name} does not currently show a clear MA20/MA50 directional relationship.")

    section("Price & Moving Averages")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["close_price"], mode="lines", name="Close Price",
                             line=dict(color=C["accent"], width=2),
                             hovertemplate="Date: %{x}<br>Close: ₹%{y:,.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"], mode="lines", name="MA20",
                             line=dict(color=C["ma20"], width=1.6),
                             hovertemplate="Date: %{x}<br>MA20: ₹%{y:,.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ma50"], mode="lines", name="MA50",
                             line=dict(color=C["ma50"], width=1.6),
                             hovertemplate="Date: %{x}<br>MA50: ₹%{y:,.2f}<extra></extra>"))
    fig.update_layout(title=f"{name} — Price Trend", xaxis_title="Date", yaxis_title="Price",
                      legend=dict(orientation="h", y=1.08))
    show(fig, 520)

    section("Recent Price Data Labels")
    fig = px.bar(df.tail(20), x="date", y="close_price", text="close_price",
                 title="Latest 20 Trading Sessions")
    fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside", cliponaxis=False,
                      textfont=dict(size=10), marker_color=C["accent"])
    show(fig, 440)

    col1, col2 = st.columns(2)
    with col1:
        section("Trading Activity")
        vol_col = "no.of_shares"
        if vol_col in df.columns:
            fig = px.bar(df.tail(30), x="date", y=vol_col, text=vol_col,
                         title="Trading Volume — Latest 30 Sessions")
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False,
                              textfont=dict(size=9), marker_color=C["ma20"])
            show(fig, 440)
        else:
            st.info("Trading-share column is not available.")
    with col2:
        section("Daily Returns")
        rets = df.tail(30).dropna(subset=["daily_return"])
        fig = px.bar(rets, x="date", y="daily_return", text="daily_return",
                     title="Daily Return — Latest 30 Sessions")
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside", cliponaxis=False,
                          textfont=dict(size=9), marker_color=signed_colors(rets["daily_return"]))
        show(fig, 440)

    section("Risk & Stability Analysis")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Positive Days", f"{m['Positive Days %']:.2f}%", "Days with positive close-to-close return", C["up"])
    with c2: metric_card("Worst Day", f"{m['Worst Day %']:.2f}%", "Largest daily decline", C["down"])
    with c3: metric_card("Best Day", f"{m['Best Day %']:.2f}%", "Largest daily increase", C["up"])
    with c4: metric_card("Signal Events", f"{m['Buy Signals'] + m['Sell Signals']:,}", "Buy + Sell crossovers")

    section("Trading Signal Analysis")
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Buy Signals", f"{m['Buy Signals']:,}", color=C["up"])
    with c2: metric_card("Sell Signals", f"{m['Sell Signals']:,}", color=C["down"])
    with c3: metric_card("Hold Sessions", f"{m['Hold Sessions']:,}", color=C["muted"])

    sig = df.dropna(subset=["ma20", "ma50"]).tail(150)
    buys, sells = sig[sig["signal"] == "Buy"], sig[sig["signal"] == "Sell"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sig["date"], y=sig["ma20"], mode="lines", name="MA20",
                             line=dict(color=C["ma20"], width=2)))
    fig.add_trace(go.Scatter(x=sig["date"], y=sig["ma50"], mode="lines", name="MA50",
                             line=dict(color=C["ma50"], width=2)))
    fig.add_trace(go.Scatter(x=buys["date"], y=buys["ma20"], mode="markers+text",
                             text=["BUY"] * len(buys), textposition="top center", name="Buy Signal",
                             textfont=dict(color=C["up"], size=11),
                             marker=dict(size=13, symbol="triangle-up", color=C["up"],
                                         line=dict(width=1, color=C["bg"]))))
    fig.add_trace(go.Scatter(x=sells["date"], y=sells["ma20"], mode="markers+text",
                             text=["SELL"] * len(sells), textposition="bottom center", name="Sell Signal",
                             textfont=dict(color=C["down"], size=11),
                             marker=dict(size=13, symbol="triangle-down", color=C["down"],
                                         line=dict(width=1, color=C["bg"]))))
    fig.update_layout(title=f"{name} — Moving Average Signals", xaxis_title="Date",
                      yaxis_title="Moving Average")
    show(fig, 500)

    section("Analytical Recommendations")
    if m["Trend"] == "Bullish":
        recommendation("Trend Monitoring",
                       f"{name} currently has a positive MA20/MA50 relationship. Monitor trend continuation "
                       "rather than relying on the latest closing price alone.")
    else:
        recommendation("Momentum Monitoring",
                       f"{name} does not currently have a bullish MA20/MA50 relationship. Additional confirmation "
                       "would help before reading recent moves as a sustained positive trend.")

    if m["Volatility %"] > 2:
        recommendation("Risk Control",
                       f"Daily volatility is relatively high at {m['Volatility %']:.2f}%. Any analytical strategy "
                       "should account for larger day-to-day price movements.")
    else:
        recommendation("Historical Stability",
                       f"Daily volatility is {m['Volatility %']:.2f}%, relatively contained within this six-stock "
                       "comparison, indicating a steadier historical price path.")

    if m["Max Drawdown %"] < -30:
        recommendation("Drawdown Awareness",
                       f"The maximum historical drawdown reached {m['Max Drawdown %']:.2f}%. Interpret long-term "
                       "returns alongside the potential size of historical declines.")

    if m["Worst Day %"] < -10:
        warning("Extreme Daily Movement",
                f"The largest daily decline was {m['Worst Day %']:.2f}%. Check for corporate actions or other "
                "market events before using raw prices for long-term comparisons.")

    st.download_button("⬇ Download Complete Stock Analysis", df.to_csv(index=False),
                       f"{selected}_analysis.csv", "text/csv")

# =========================================================
# CROSS-STOCK INSIGHTS
# =========================================================
elif page == "Cross-Stock Insights":
    page_header("Cross-Stock Insights",
                "Compare performance, risk, drawdown and trend structure across all six companies.")

    comparison = build_comparison()

    section("Analytical Scorecard")
    display_df = comparison.copy()
    num_cols = ["First Price", "Latest Price", "Return %", "Volatility %", "Positive Days %",
                "Max Drawdown %", "Worst Day %", "Best Day %", "MA20", "MA50"]
    display_df[num_cols] = display_df[num_cols].round(2)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.download_button("⬇ Download Cross-Stock Scorecard", display_df.to_csv(index=False),
                       "cross_stock_scorecard.csv", "text/csv")

    section("Historical Return Comparison")
    hbar(comparison, "Return %", "First-to-Last Return", lambda d: signed_colors(d["Return %"]))

    section("Historical Volatility")
    hbar(comparison, "Volatility %", "Daily Return Volatility", C["accent"])

    section("Maximum Drawdown")
    hbar(comparison, "Max Drawdown %", "Historical Peak-to-Trough Drawdown", C["down"])

    best = comparison.loc[comparison["Return %"].idxmax()]
    worst = comparison.loc[comparison["Return %"].idxmin()]
    stable = comparison.loc[comparison["Volatility %"].idxmin()]
    volatile = comparison.loc[comparison["Volatility %"].idxmax()]
    deepest = comparison.loc[comparison["Max Drawdown %"].idxmin()]

    section("Business Insights")
    insight("🏆 Return Leadership",
            f"{best['Stock']} ranks first by historical price return at {best['Return %']:.2f}%, "
            f"while {worst['Stock']} ranks last at {worst['Return %']:.2f}%.")
    insight("🛡️ Stability",
            f"{stable['Stock']} has the lowest daily volatility ({stable['Volatility %']:.2f}%), making it the "
            "most stable stock in this historical comparison.")
    insight("⚡ Volatility",
            f"{volatile['Stock']} has the highest daily volatility ({volatile['Volatility %']:.2f}%). Its return "
            "should be read together with its higher historical price variability.")
    insight("📉 Drawdown Risk",
            f"{deepest['Stock']} experienced the largest maximum drawdown at {deepest['Max Drawdown %']:.2f}%, "
            "highlighting the importance of evaluating downside risk alongside return.")

    section("Portfolio-Style Analytical Recommendations")
    recommendation("Balance Growth and Stability",
                   f"Do not rank stocks by return alone. {best['Stock']} leads on return, while {stable['Stock']} "
                   "has the lowest historical volatility. Evaluate both before choosing a preferred stock.")
    recommendation("Investigate Outliers",
                   "Large differences in return, volatility and drawdown should be investigated using company "
                   "fundamentals, corporate actions, market events and sector information.")
    recommendation("Use Multiple Metrics",
                   "The most useful framework combines return, volatility, maximum drawdown, positive-day ratio "
                   "and trend structure rather than relying on one KPI.")
    recommendation("Validate Before Deployment",
                   "The SQL crossover strategy demonstrates analytical skills, but a production strategy would "
                   "need backtesting, transaction-cost assumptions and out-of-sample validation.")

# =========================================================
# SQL TASKS
# =========================================================
elif page == "SQL Tasks":
    page_header("SQL Analysis Tasks", "All 13 validated SQL tasks executed directly against the SQLite database.")

    task = st.selectbox("Select SQL Task", list(TASKS.keys()))
    sql = TASKS[task]
    st.code(sql, language="sql")

    try:
        result = run_sql(sql)
        st.success(f"Query executed successfully — {len(result):,} rows returned.")
        st.dataframe(result, use_container_width=True, hide_index=True)
        st.download_button("⬇ Download SQL Result", result.to_csv(index=False),
                           "sql_task_result.csv", "text/csv")
    except Exception as e:
        st.error(f"SQL execution error: {e}")

# =========================================================
# SQL PLAYGROUND
# =========================================================
elif page == "SQL Playground":
    page_header("SQL Playground", "Explore the stock database using custom SQL queries.")

    default_sql = """SELECT
    date,
    close_price
FROM bajaj_auto
ORDER BY date DESC
LIMIT 20;"""
    query = st.text_area("SQL Query", value=default_sql, height=230)

    if st.button("▶ Run SQL", type="primary"):
        try:
            result = run_sql(query)
            st.success(f"Query executed successfully — {len(result):,} rows returned.")
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.download_button("⬇ Download Query Result", result.to_csv(index=False),
                               "sql_query_result.csv", "text/csv")
        except Exception as e:
            st.error(f"SQL Error: {e}")

    section("Database Tables")
    rows = []
    for table, label in STOCKS.items():
        d = load_data(table)
        rows.append({"Table": table, "Stock": label, "Rows": len(d), "Columns": len(d.columns),
                     "Start": d["date"].min().strftime("%Y-%m-%d"),
                     "End": d["date"].max().strftime("%Y-%m-%d")})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# =========================================================
# DATA EXPLORER
# =========================================================
elif page == "Data Explorer":
    page_header("Data Explorer", "Explore the cleaned datasets stored in SQLite.")

    selected = st.selectbox("Select Dataset", list(STOCKS.keys()), format_func=lambda x: STOCKS[x])
    df = load_data(selected)

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Rows", f"{len(df):,}")
    with c2: metric_card("Columns", f"{len(df.columns):,}")
    with c3: metric_card("Missing Values", f"{df.isna().sum().sum():,}")
    with c4: metric_card("Date Range", f"{df['date'].min().year}–{df['date'].max().year}")

    section("Dataset Preview")
    st.dataframe(df, use_container_width=True, height=620, hide_index=True)
    st.download_button("⬇ Download Dataset", df.to_csv(index=False),
                       f"{selected}_data.csv", "text/csv")

    section("Data Quality Summary")
    quality = pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(t) for t in df.dtypes],
        "Missing Values": [int(df[c].isna().sum()) for c in df.columns],
        "Unique Values": [int(df[c].nunique()) for c in df.columns],
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)