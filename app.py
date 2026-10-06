import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SQL Stock Market Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "stock_market.db"
CLEANED_DIR = BASE_DIR / "cleaned_data"


# ============================================================
# STOCK CONFIGURATION
# ============================================================

STOCKS = {
    "bajaj_auto": "Bajaj Auto",
    "eicher_motors": "Eicher Motors",
    "hero_motocorp": "Hero Motocorp",
    "infosys": "Infosys",
    "tcs": "TCS",
    "tvs_motors": "TVS Motors",
}

STOCK_LIST = list(STOCKS.keys())


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1.5rem 1.8rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
        background: linear-gradient(
            135deg,
            rgba(35, 38, 58, 0.95),
            rgba(20, 22, 35, 0.98)
        );
        border: 1px solid rgba(255,255,255,0.08);
    }

    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
    }

    .hero p {
        margin-top: 0.5rem;
        color: #b8bfd3;
        font-size: 1rem;
    }

    .metric-card {
        padding: 1.1rem;
        border-radius: 14px;
        background: rgba(35, 38, 58, 0.8);
        border: 1px solid rgba(255,255,255,0.08);
        min-height: 120px;
    }

    .metric-title {
        color: #aeb6cc;
        font-size: 0.85rem;
    }

    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        margin-top: 0.35rem;
    }

    .metric-sub {
        color: #8d96ad;
        font-size: 0.78rem;
        margin-top: 0.3rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.7rem;
    }

    .insight-box {
        padding: 1rem 1.1rem;
        border-radius: 12px;
        background: rgba(35, 38, 58, 0.75);
        border: 1px solid rgba(255,255,255,0.07);
        margin-bottom: 0.7rem;
    }

    .small-muted {
        color: #929bb0;
        font-size: 0.85rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Create/rebuild SQLite database from cleaned CSV files.

    This is important for Streamlit Cloud because stock_market.db
    is intentionally excluded from GitHub.
    """

    conn = sqlite3.connect(DB_PATH)

    try:
        for table in STOCK_LIST:
            csv_path = CLEANED_DIR / f"{table}.csv"

            if not csv_path.exists():
                st.error(f"Missing cleaned CSV: {csv_path}")
                continue

            df = pd.read_csv(csv_path)

            df.to_sql(
                table,
                conn,
                if_exists="replace",
                index=False,
            )

    finally:
        conn.close()


# Always make sure the database exists.
initialize_database()


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


@st.cache_data
def load_data(table):
    """Load one stock table from SQLite."""

    if table not in STOCK_LIST:
        raise ValueError("Invalid stock table.")

    conn = get_connection()

    try:
        df = pd.read_sql_query(
            f"SELECT * FROM {table}",
            conn,
        )
    finally:
        conn.close()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


@st.cache_data
def run_sql(query):
    conn = get_connection()

    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def get_table_columns(table):
    conn = get_connection()

    try:
        result = pd.read_sql_query(
            f"PRAGMA table_info({table})",
            conn,
        )
    finally:
        conn.close()

    return result


# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_stock_data(table):
    df = load_data(table).copy()

    if df.empty:
        return df

    df = df.sort_values("date").reset_index(drop=True)

    # Numeric columns
    numeric_candidates = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "wap",
        "no.of_shares",
        "no._of_trades",
        "total_turnover_(rs.)",
        "deliverable_quantity",
        "%_deli._qty_to_traded_qty",
        "spread_high-low",
        "spread_close-open",
        "spread_high_low",
        "spread_close_open",
    ]

    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    # Moving averages
    if "close_price" in df.columns:
        df["MA20"] = (
            df["close_price"]
            .rolling(window=20, min_periods=20)
            .mean()
        )

        df["MA50"] = (
            df["close_price"]
            .rolling(window=50, min_periods=50)
            .mean()
        )

        # Daily return
        df["Daily Return %"] = (
            df["close_price"]
            .pct_change()
            * 100
        )

        # Buy / Sell / Hold strategy
        df["Signal"] = "Hold"

        buy_condition = (
            (df["MA20"] > df["MA50"])
            & (df["MA20"].shift(1) <= df["MA50"].shift(1))
        )

        sell_condition = (
            (df["MA20"] < df["MA50"])
            & (df["MA20"].shift(1) >= df["MA50"].shift(1))
        )

        df.loc[buy_condition, "Signal"] = "Buy"
        df.loc[sell_condition, "Signal"] = "Sell"

    return df


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(table):
    df = prepare_stock_data(table)

    if df.empty:
        return {
            "Stock": STOCKS[table],
            "Start Price": np.nan,
            "Latest Price": np.nan,
            "Return %": np.nan,
            "Volatility %": np.nan,
            "High": np.nan,
            "Low": np.nan,
            "Buy Signals": 0,
            "Sell Signals": 0,
        }

    start_price = df["close_price"].iloc[0]
    latest_price = df["close_price"].iloc[-1]

    total_return = (
        (latest_price / start_price) - 1
    ) * 100

    volatility = (
        df["Daily Return %"]
        .std()
        if "Daily Return %" in df.columns
        else np.nan
    )

    return {
        "Stock": STOCKS[table],
        "Start Price": start_price,
        "Latest Price": latest_price,
        "Return %": total_return,
        "Volatility %": volatility,
        "High": df["close_price"].max(),
        "Low": df["close_price"].min(),
        "Buy Signals": int(
            (df["Signal"] == "Buy").sum()
        ),
        "Sell Signals": int(
            (df["Signal"] == "Sell").sum()
        ),
    }


@st.cache_data
def build_comparison():
    return pd.DataFrame(
        [
            calculate_metrics(table)
            for table in STOCK_LIST
        ]
    )


comparison = build_comparison()


# ============================================================
# SQL TASKS
# ============================================================

def task_1():
    rows = []

    for table, name in STOCKS.items():
        df = load_data(table)

        rows.append(
            {
                "Stock": name,
                "Rows": len(df),
                "Start Date": df["date"].min(),
                "End Date": df["date"].max(),
                "Min Close": df["close_price"].min(),
                "Max Close": df["close_price"].max(),
            }
        )

    return pd.DataFrame(rows)


def task_2():
    df = load_data("eicher_motors")

    return (
        df[
            [
                "date",
                "close_price",
            ]
        ]
        .sort_values(
            "close_price",
            ascending=False,
        )
        .head(5)
    )


def task_3():
    df = load_data("tcs").copy()

    df["Year"] = df["date"].dt.year

    return (
        df.groupby("Year")["close_price"]
        .mean()
        .reset_index(name="Average Close")
    )


def task_4():
    rows = []

    for table, name in STOCKS.items():
        df = load_data(table)

        rows.append(
            {
                "Stock": name,
                "NULL Deliverable Quantity": int(
                    df["deliverable_quantity"].isna().sum()
                ),
            }
        )

    return pd.DataFrame(rows)


def task_5():
    df = prepare_stock_data("bajaj_auto")

    return df[
        [
            "date",
            "close_price",
            "MA20",
            "MA50",
        ]
    ].tail(100)


def task_6():
    frames = []

    for table, name in STOCKS.items():
        df = load_data(table)[
            [
                "date",
                "close_price",
            ]
        ].copy()

        df = df.rename(
            columns={
                "close_price": f"{table}_close"
            }
        )

        frames.append(df)

    master = frames[0]

    for frame in frames[1:]:
        master = master.merge(
            frame,
            on="date",
            how="outer",
        )

    return master.sort_values("date")


def task_7():
    frames = []

    for table, name in STOCKS.items():
        df = prepare_stock_data(table).copy()

        signal_df = df[
            [
                "date",
                "close_price",
                "MA20",
                "MA50",
                "Signal",
            ]
        ].copy()

        signal_df.insert(
            0,
            "Stock",
            name,
        )

        frames.append(signal_df)

    return pd.concat(
        frames,
        ignore_index=True,
    )


def task_8():
    signals = task_7()

    return (
        signals[
            signals["Signal"].isin(
                ["Buy", "Sell"]
            )
        ]
        .groupby("Signal")
        .size()
        .reset_index(name="Count")
    )


def task_9():
    signals = task_7()

    return signals[
        signals["date"]
        == pd.Timestamp("2018-06-21")
    ]


def task_10():
    signals = task_7()

    result = (
        signals[
            signals["Signal"].isin(
                ["Buy", "Sell"]
            )
        ]
        .groupby(
            ["Stock", "Signal"]
        )
        .size()
        .unstack(
            fill_value=0
        )
        .reset_index()
    )

    return result


def task_11():
    rows = []

    for table, name in STOCKS.items():
        df = load_data(table)

        first_price = df["close_price"].iloc[0]
        last_price = df["close_price"].iloc[-1]

        return_pct = (
            (last_price / first_price) - 1
        ) * 100

        rows.append(
            {
                "Stock": name,
                "First Close": first_price,
                "Last Close": last_price,
                "Return %": return_pct,
            }
        )

    return pd.DataFrame(rows)


def task_12():
    frames = []

    for table, name in STOCKS.items():
        df = load_data(table).copy()

        df["Daily Return %"] = (
            df["close_price"]
            .pct_change()
            * 100
        )

        df["Stock"] = name

        frames.append(
            df[
                [
                    "Stock",
                    "date",
                    "close_price",
                    "Daily Return %",
                ]
            ]
        )

    all_returns = pd.concat(
        frames,
        ignore_index=True,
    )

    return all_returns.sort_values(
        "Daily Return %"
    ).head(10)


def task_13():
    """
    Corporate-action analysis.

    The student guide identifies large price jumps in
    TCS and Infosys and describes a 1:1 bonus adjustment,
    where pre-event prices are divided by 2.

    This function compares original and adjusted
    first-to-last returns.
    """

    rows = []

    for table in ["tcs", "infosys"]:
        df = load_data(table).copy()

        first_price = df["close_price"].iloc[0]
        last_price = df["close_price"].iloc[-1]

        original_return = (
            (last_price / first_price) - 1
        ) * 100

        adjusted = df.copy()

        # Apply 1:1 bonus adjustment to prices
        # before the identified corporate-action period.
        if table == "tcs":
            event_date = pd.Timestamp("2017-06-15")
        else:
            event_date = pd.Timestamp("2018-09-01")

        adjusted.loc[
            adjusted["date"] < event_date,
            "close_price",
        ] /= 2

        adjusted_first = adjusted[
            "close_price"
        ].iloc[0]

        adjusted_last = adjusted[
            "close_price"
        ].iloc[-1]

        adjusted_return = (
            (adjusted_last / adjusted_first) - 1
        ) * 100

        rows.append(
            {
                "Stock": STOCKS[table],
                "Original Return %": original_return,
                "Adjusted Return %": adjusted_return,
                "Adjustment": "1:1 bonus adjustment",
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📊 Stock Analytics")

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Stock Analysis",
        "Cross-Stock Insights",
        "SQL Tasks",
        "SQL Playground",
        "Data Explorer",
    ],
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "SQL Stock Market Analytics"
)

st.sidebar.caption(
    "2015–2018 historical market analysis"
)


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>📈 SQL Stock Market Analytics</h1>
        <p>
            Data-driven analysis of six Indian stocks using
            SQL, Python, Pandas and Streamlit.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        '<div class="section-title">Portfolio Overview</div>',
        unsafe_allow_html=True,
    )

    total_stocks = len(STOCK_LIST)

    best_row = comparison.loc[
        comparison["Return %"].idxmax()
    ]

    worst_row = comparison.loc[
        comparison["Return %"].idxmin()
    ]

    avg_return = comparison["Return %"].mean()

    avg_volatility = comparison[
        "Volatility %"
    ].mean()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Stocks Analyzed",
            total_stocks,
        )

    with c2:
        st.metric(
            "Best Performer",
            best_row["Stock"],
            f"{best_row['Return %']:.2f}%",
        )

    with c3:
        st.metric(
            "Average Return",
            f"{avg_return:.2f}%",
        )

    with c4:
        st.metric(
            "Average Daily Volatility",
            f"{avg_volatility:.2f}%",
        )

    st.markdown("---")

    # Performance chart
    st.subheader("📊 Stock Performance")

    chart_df = comparison.sort_values(
        "Return %",
        ascending=False,
    )

    fig = px.bar(
        chart_df,
        x="Stock",
        y="Return %",
        text="Return %",
        title="First-to-Last Price Return",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=450,
        xaxis_title="Stock",
        yaxis_title="Return (%)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("📋 Performance Ranking")

    display_df = comparison.copy()

    for col in [
        "Start Price",
        "Latest Price",
        "High",
        "Low",
    ]:
        display_df[col] = display_df[col].round(2)

    display_df["Return %"] = display_df[
        "Return %"
    ].round(2)

    display_df["Volatility %"] = display_df[
        "Volatility %"
    ].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    st.subheader("💡 Business Insights")

    best = best_row["Stock"]
    worst = worst_row["Stock"]

    st.markdown(
        f"""
        <div class="insight-box">
            <b>🏆 Strongest performer:</b>
            {best} generated the highest first-to-last price return
            among the six analyzed stocks.
        </div>

        <div class="insight-box">
            <b>📉 Weakest performer:</b>
            {worst} generated the lowest first-to-last return.
        </div>

        <div class="insight-box">
            <b>⚠️ Risk consideration:</b>
            Daily-return volatility should be considered alongside
            absolute returns when evaluating performance.
        </div>

        <div class="insight-box">
            <b>📌 Strategy note:</b>
            Moving-average crossover signals are trend-following
            indicators and should not be treated as standalone
            investment recommendations.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# STOCK ANALYSIS
# ============================================================

elif page == "Stock Analysis":

    st.subheader("🔎 Individual Stock Analysis")

    selected_stock = st.selectbox(
        "Select Stock",
        STOCK_LIST,
        format_func=lambda x: STOCKS[x],
    )

    df = prepare_stock_data(
        selected_stock
    )

    latest = df.iloc[-1]

    latest_price = latest["close_price"]
    previous_price = (
        df["close_price"].iloc[-2]
        if len(df) > 1
        else latest_price
    )

    daily_change = (
        (latest_price / previous_price) - 1
    ) * 100

    total_return = (
        (
            latest_price
            / df["close_price"].iloc[0]
        )
        - 1
    ) * 100

    buy_count = int(
        (df["Signal"] == "Buy").sum()
    )

    sell_count = int(
        (df["Signal"] == "Sell").sum()
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Latest Close",
            f"{latest_price:,.2f}",
        )

    with c2:
        st.metric(
            "Daily Change",
            f"{daily_change:.2f}%",
        )

    with c3:
        st.metric(
            "Total Return",
            f"{total_return:.2f}%",
        )

    with c4:
        st.metric(
            "Latest Signal",
            latest["Signal"],
        )

    st.markdown("---")

    # Price chart
    st.subheader(
        f"📈 {STOCKS[selected_stock]} Price & Moving Averages"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close_price"],
            mode="lines",
            name="Close Price",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["MA20"],
            mode="lines",
            name="MA20",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["MA50"],
            mode="lines",
            name="MA50",
        )
    )

    buy_df = df[
        df["Signal"] == "Buy"
    ]

    sell_df = df[
        df["Signal"] == "Sell"
    ]

    fig.add_trace(
        go.Scatter(
            x=buy_df["date"],
            y=buy_df["close_price"],
            mode="markers",
            name="Buy",
            marker=dict(
                size=10,
                symbol="triangle-up",
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=sell_df["date"],
            y=sell_df["close_price"],
            mode="markers",
            name="Sell",
            marker=dict(
                size=10,
                symbol="triangle-down",
            ),
        )
    )

    fig.update_layout(
        height=600,
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Price",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # Recent data
    st.subheader("📋 Recent Price Data")

    recent = df[
        [
            "date",
            "close_price",
            "MA20",
            "MA50",
            "Daily Return %",
            "Signal",
        ]
    ].tail(20).copy()

    recent["close_price"] = recent[
        "close_price"
    ].round(2)

    recent["MA20"] = recent[
        "MA20"
    ].round(2)

    recent["MA50"] = recent[
        "MA50"
    ].round(2)

    recent["Daily Return %"] = recent[
        "Daily Return %"
    ].round(2)

    st.dataframe(
        recent.sort_values(
            "date",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Trading activity
    st.subheader("📊 Trading Activity")

    activity_columns = []

    for col in [
        "no.of_shares",
        "no._of_trades",
        "total_turnover_(rs.)",
    ]:
        if col in df.columns:
            activity_columns.append(col)

    if activity_columns:

        activity = df[
            ["date"] + activity_columns
        ].tail(100)

        fig_activity = px.line(
            activity,
            x="date",
            y=activity_columns,
            title="Recent Trading Activity",
        )

        fig_activity.update_layout(
            height=450,
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_activity,
            use_container_width=True,
        )

    # Returns
    st.subheader("📉 Daily Returns")

    returns = df[
        ["date", "Daily Return %"]
    ].dropna()

    fig_returns = px.line(
        returns,
        x="date",
        y="Daily Return %",
        title="Daily Percentage Returns",
    )

    fig_returns.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Daily Return (%)",
    )

    st.plotly_chart(
        fig_returns,
        use_container_width=True,
    )

    # Recommendations
    st.subheader("💡 Analytical Recommendation")

    if latest["Signal"] == "Buy":
        message = (
            "The latest moving-average crossover is bullish. "
            "The short-term MA20 is above MA50 and a recent "
            "golden-cross signal was detected."
        )

    elif latest["Signal"] == "Sell":
        message = (
            "The latest moving-average crossover is bearish. "
            "The short-term MA20 is below MA50 and a recent "
            "death-cross signal was detected."
        )

    else:
        message = (
            "There is currently no fresh crossover signal. "
            "The moving-average strategy is in a holding state."
        )

    st.info(message)

    st.caption(
        "This is an analytical dashboard, not financial advice."
    )


# ============================================================
# CROSS STOCK INSIGHTS
# ============================================================

elif page == "Cross-Stock Insights":

    st.subheader("🏆 Cross-Stock Comparison")

    comparison_chart = comparison.sort_values(
        "Return %",
        ascending=False,
    )

    fig = px.bar(
        comparison_chart,
        x="Stock",
        y="Return %",
        color="Volatility %",
        text="Return %",
        title="Return vs Volatility",
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=500,
        xaxis_title="Stock",
        yaxis_title="Return (%)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.subheader("📊 Risk vs Return")

    fig_scatter = px.scatter(
        comparison,
        x="Volatility %",
        y="Return %",
        text="Stock",
        size="Latest Price",
        title="Risk vs Return",
    )

    fig_scatter.update_traces(
        textposition="top center"
    )

    fig_scatter.update_layout(
        height=500,
        xaxis_title="Daily Volatility (%)",
        yaxis_title="Total Return (%)",
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True,
    )

    st.subheader("📋 Comparison Table")

    st.dataframe(
        comparison.round(2),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("🎯 Signal Activity")

    signal_summary = []

    for table, name in STOCKS.items():

        df = prepare_stock_data(table)

        signal_summary.append(
            {
                "Stock": name,
                "Buy Signals": int(
                    (df["Signal"] == "Buy").sum()
                ),
                "Sell Signals": int(
                    (df["Signal"] == "Sell").sum()
                ),
                "Hold Days": int(
                    (df["Signal"] == "Hold").sum()
                ),
            }
        )

    signal_df = pd.DataFrame(
        signal_summary
    )

    st.dataframe(
        signal_df,
        use_container_width=True,
        hide_index=True,
    )

    fig_signal = px.bar(
        signal_df,
        x="Stock",
        y=[
            "Buy Signals",
            "Sell Signals",
        ],
        barmode="group",
        title="Buy vs Sell Signals",
    )

    fig_signal.update_layout(
        height=450,
    )

    st.plotly_chart(
        fig_signal,
        use_container_width=True,
    )


# ============================================================
# SQL TASKS
# ============================================================

elif page == "SQL Tasks":

    st.subheader("🧮 SQL Analysis Tasks")

    task = st.selectbox(
        "Select Analysis Task",
        [
            "Task 1 — Stock Overview",
            "Task 2 — Eicher Top 5 Closing Prices",
            "Task 3 — TCS Yearly Average Close",
            "Task 4 — NULL Deliverable Quantity",
            "Task 5 — 20/50 Day Moving Averages",
            "Task 6 — Master Table",
            "Task 7 — Buy/Sell/Hold Signals",
            "Task 8 — Signal Counts",
            "Task 9 — Signal on 2018-06-21",
            "Task 10 — Signals Across All Stocks",
            "Task 11 — First-to-Last Return",
            "Task 12 — Worst Daily Drops",
            "Task 13 — Corporate Action Analysis",
        ],
    )

    task_functions = {
        "Task 1 — Stock Overview": task_1,
        "Task 2 — Eicher Top 5 Closing Prices": task_2,
        "Task 3 — TCS Yearly Average Close": task_3,
        "Task 4 — NULL Deliverable Quantity": task_4,
        "Task 5 — 20/50 Day Moving Averages": task_5,
        "Task 6 — Master Table": task_6,
        "Task 7 — Buy/Sell/Hold Signals": task_7,
        "Task 8 — Signal Counts": task_8,
        "Task 9 — Signal on 2018-06-21": task_9,
        "Task 10 — Signals Across All Stocks": task_10,
        "Task 11 — First-to-Last Return": task_11,
        "Task 12 — Worst Daily Drops": task_12,
        "Task 13 — Corporate Action Analysis": task_13,
    }

    result = task_functions[task]()

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = result.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Result",
        csv_data,
        file_name="sql_task_result.csv",
        mime="text/csv",
    )


# ============================================================
# SQL PLAYGROUND
# ============================================================

elif page == "SQL Playground":

    st.subheader("🧑‍💻 SQL Playground")

    st.caption(
        "Run read-only SQL queries against the SQLite database."
    )

    default_query = """
SELECT
    date,
    close_price
FROM bajaj_auto
ORDER BY date DESC
LIMIT 20;
""".strip()

    query = st.text_area(
        "SQL Query",
        value=default_query,
        height=180,
    )

    if st.button(
        "▶ Run Query",
        type="primary",
    ):

        cleaned_query = query.strip().lower()

        blocked = [
            "drop ",
            "delete ",
            "update ",
            "insert ",
            "alter ",
            "replace ",
            "create ",
            "attach ",
            "detach ",
        ]

        if any(
            word in cleaned_query
            for word in blocked
        ):
            st.error(
                "Only read-only SELECT queries are allowed."
            )

        elif not (
            cleaned_query.startswith("select")
            or cleaned_query.startswith("with")
            or cleaned_query.startswith("pragma")
        ):
            st.error(
                "Please enter a SELECT, WITH, or PRAGMA query."
            )

        else:
            try:
                result = run_sql(query)

                st.success(
                    f"Query executed successfully — "
                    f"{len(result):,} rows returned."
                )

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True,
                )

            except Exception as e:
                st.error(
                    f"SQL Error: {e}"
                )


# ============================================================
# DATA EXPLORER
# ============================================================

elif page == "Data Explorer":

    st.subheader("🗃️ Data Explorer")

    selected_table = st.selectbox(
        "Select Table",
        STOCK_LIST,
        format_func=lambda x: STOCKS[x],
    )

    df = load_data(
        selected_table
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Rows",
            f"{len(df):,}",
        )

    with c2:
        st.metric(
            "Columns",
            f"{len(df.columns):,}",
        )

    with c3:
        missing = int(
            df.isna().sum().sum()
        )

        st.metric(
            "Missing Values",
            f"{missing:,}",
        )

    st.markdown("---")

    st.subheader("📋 Dataset Preview")

    st.dataframe(
        df.tail(100),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("🔍 Column Information")

    info = pd.DataFrame(
        {
            "Column": df.columns,
            "Data Type": [
                str(dtype)
                for dtype in df.dtypes
            ],
            "Missing Values": [
                int(df[col].isna().sum())
                for col in df.columns
            ],
            "Unique Values": [
                int(df[col].nunique())
                for col in df.columns
            ],
        }
    )

    st.dataframe(
        info,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("📊 Numeric Summary")

    numeric_df = df.select_dtypes(
        include=np.number
    )

    if not numeric_df.empty:
        st.dataframe(
            numeric_df.describe().T.round(2),
            use_container_width=True,
        )

    st.download_button(
        "⬇️ Download Current Dataset",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_table}.csv",
        mime="text/csv",
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "SQL Stock Market Analytics • Built with Python, SQL, Pandas, Plotly and Streamlit"
)

st.caption(
    "Historical analysis only — not financial advice."
)


   
