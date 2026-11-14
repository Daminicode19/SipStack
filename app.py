import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
# Page Configuration
st.set_page_config(
    page_title="SipStack | NSE Analytics",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>

.stApp {
    background-color: #101827;
    color: #F1F5F9;
}

[data-testid="stSidebar"] {
    background-color: #172235;
}

h1, h2, h3 {
    color: #F8FAFC;
}

p, label {
    color: #CBD5E1;
}

div[data-testid="stMetric"] {
    background-color: #1E293B;
    border: 1px solid #334155;
    padding: 18px;
    border-radius: 12px;
}

div[data-testid="stMetricValue"] {
    color: #34D399;
}

.stButton button {
    background-color: #059669;
    color: white;
    border-radius: 8px;
    border: none;
}

.stButton button:hover {
    background-color: #047857;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# App Title
st.markdown("""
<div style="background: linear-gradient(135deg, #172235, #1E293B); padding: 25px 30px; border-radius: 15px; border-left: 5px solid #10B981; margin-bottom: 25px;">
<h1 style="color: #34D399; font-size: 36px; margin: 0;">📈 SIPSTACK</h1>
<p style="color: #CBD5E1; font-size: 16px; margin: 5px 0 0 0;">NSE Stock Analysis & Backtesting Dashboard</p>
</div>
""", unsafe_allow_html=True)
st.header("Stock Analysis")

# Stock Selection
ticker = st.text_input("Enter NSE Stock Symbol", "RELIANCE.NS")
st.write("Selected Stock:", ticker)

# Download Stock Data
data = yf.download(
    ticker,
    period="2y",
    interval="1wk",
    auto_adjust=True
)

# Handle MultiIndex Columns
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if not data.empty:

    st.subheader(f"{ticker} - Historical Data")

    # Moving Average
    data["MA_20"] = data["Close"].rolling(window=20).mean()

    # Wilder RSI
    data["Price_Change"] = data["Close"].diff()
    data["Gain"] = data["Price_Change"].clip(lower=0)
    data["Loss"] = -data["Price_Change"].clip(upper=0)

    initial_avg_gain = data["Gain"].iloc[1:15].mean()
    initial_avg_loss = data["Loss"].iloc[1:15].mean()

    data["Wilder_Avg_Gain"] = float("nan")
    data["Wilder_Avg_Loss"] = float("nan")

    if len(data) >= 15:
        data.iloc[14, data.columns.get_loc("Wilder_Avg_Gain")] = initial_avg_gain
        data.iloc[14, data.columns.get_loc("Wilder_Avg_Loss")] = initial_avg_loss

        for i in range(15, len(data)):
            data.iloc[i, data.columns.get_loc("Wilder_Avg_Gain")] = (
                (data["Wilder_Avg_Gain"].iloc[i-1] * 13 + data["Gain"].iloc[i]) / 14
            )

            data.iloc[i, data.columns.get_loc("Wilder_Avg_Loss")] = (
                (data["Wilder_Avg_Loss"].iloc[i-1] * 13 + data["Loss"].iloc[i]) / 14
            )

    data["Wilder_RS"] = (
        data["Wilder_Avg_Gain"] / data["Wilder_Avg_Loss"]
    )

    data["Wilder_RSI"] = 100 - (100 / (1 + data["Wilder_RS"]))

    # Mean Reversion Signals
    data["MR_Entry_Signal"] = data["Close"] <= data["MA_20"] * 0.95
    data["MR_Exit_Signal"] = data["Close"] >= data["MA_20"]

    data["MR_Entry_Event"] = (
        data["MR_Entry_Signal"] &
        ~data["MR_Entry_Signal"].shift(1).fillna(False)
    )

    data["MR_Exit_Event"] = (
        data["MR_Exit_Signal"] &
        ~data["MR_Exit_Signal"].shift(1).fillna(False)
    )

    data["MR_Entry_Execution"] = (
        data["MR_Entry_Event"].shift(1).fillna(False).astype(bool)
    )

    data["MR_Exit_Execution"] = (
        data["MR_Exit_Event"].shift(1).fillna(False).astype(bool)
    )

    # Momentum Signals
    data["Momentum_Entry_Signal"] = data["Close"] > data["MA_20"]
    data["Momentum_Exit_Signal"] = data["Close"] < data["MA_20"]

    data["Momentum_Entry_Event"] = (
        data["Momentum_Entry_Signal"] &
        ~data["Momentum_Entry_Signal"].shift(1, fill_value=False)
    )

    data["Momentum_Exit_Event"] = (
        data["Momentum_Exit_Signal"] &
        ~data["Momentum_Exit_Signal"].shift(1, fill_value=False)
    )

    data["Momentum_Entry_Execution"] = (
        data["Momentum_Entry_Event"].shift(1, fill_value=False).astype(bool)
    )

    data["Momentum_Exit_Execution"] = (
        data["Momentum_Exit_Event"].shift(1, fill_value=False).astype(bool)
    )

    # Momentum Position Tracker
    momentum_positions = []
    momentum_position = 0

    for i in range(len(data)):
        if momentum_position == 0 and data["Momentum_Entry_Execution"].iloc[i]:
            momentum_position = 1

        elif momentum_position == 1 and data["Momentum_Exit_Execution"].iloc[i]:
            momentum_position = 0

        momentum_positions.append(momentum_position)

    data["Momentum_Position"] = momentum_positions

    # Mean Reversion Position Tracker
    positions = []
    position = 0

    for i in range(len(data)):
        if position == 0 and data["MR_Entry_Execution"].iloc[i]:
            position = 1

        elif position == 1 and data["MR_Exit_Execution"].iloc[i]:
            position = 0

        positions.append(position)

    data["MR_Position"] = positions

    # Mean Reversion Trade Log
    completed_trades = []
    entry_date = None
    entry_price = None

    for i in range(len(data)):

        if data["MR_Entry_Execution"].iloc[i] and entry_date is None:
            entry_date = data.index[i]
            entry_price = data["Open"].iloc[i]

        elif data["MR_Exit_Execution"].iloc[i] and entry_date is not None:
            exit_date = data.index[i]
            exit_price = data["Open"].iloc[i]

            trade_return = (
                (exit_price / entry_price) - 1
            ) * 100

            completed_trades.append({
                "Entry Date": entry_date,
                "Entry Price": entry_price,
                "Exit Date": exit_date,
                "Exit Price": exit_price,
                "Trade Return (%)": trade_return
            })

            entry_date = None
            entry_price = None

    trade_log = pd.DataFrame(completed_trades)

    # Mean Reversion Trade Statistics
    mr_total_trades = len(trade_log)

    if not trade_log.empty:
        winning_trades = (
            trade_log["Trade Return (%)"] > 0
        ).sum()

        win_rate = (
            winning_trades / mr_total_trades
        ) * 100

        avg_trade_return = trade_log["Trade Return (%)"].mean()

    else:
        win_rate = 0
        avg_trade_return = 0

    # Momentum Trade Log
    momentum_completed_trades = []
    momentum_entry_date = None
    momentum_entry_price = None

    for i in range(len(data)):

        if (
            data["Momentum_Entry_Execution"].iloc[i]
            and momentum_entry_date is None
        ):
            momentum_entry_date = data.index[i]
            momentum_entry_price = data["Open"].iloc[i]

        elif (
            data["Momentum_Exit_Execution"].iloc[i]
            and momentum_entry_date is not None
        ):
            momentum_exit_date = data.index[i]
            momentum_exit_price = data["Open"].iloc[i]

            momentum_trade_return = (
                (momentum_exit_price / momentum_entry_price) - 1
            ) * 100

            momentum_completed_trades.append({
                "Entry Date": momentum_entry_date,
                "Entry Price": momentum_entry_price,
                "Exit Date": momentum_exit_date,
                "Exit Price": momentum_exit_price,
                "Trade Return (%)": momentum_trade_return
            })

            momentum_entry_date = None
            momentum_entry_price = None

    momentum_trade_log = pd.DataFrame(momentum_completed_trades)

    # Momentum Trade Statistics
    momentum_total_trades = len(momentum_trade_log)

    if not momentum_trade_log.empty:
        momentum_winning_trades = (
            momentum_trade_log["Trade Return (%)"] > 0
        ).sum()

        momentum_win_rate = (
            momentum_winning_trades / momentum_total_trades
        ) * 100

        momentum_avg_trade_return = (
            momentum_trade_log["Trade Return (%)"].mean()
        )

    else:
        momentum_win_rate = 0
        momentum_avg_trade_return = 0

    # Weekly Returns
    data["Open_to_Open_Return"] = (
        data["Open"].shift(-1) / data["Open"] - 1
    ) * 100

    # Mean Reversion Returns
    data["MR_Strategy_Return"] = (
        data["MR_Position"] * data["Open_to_Open_Return"]
    )

    data["MR_Cumulative_Return"] = (
        (1 + data["MR_Strategy_Return"].fillna(0) / 100).cumprod() - 1
    ) * 100

    # Momentum Returns
    data["Momentum_Strategy_Return"] = (
        data["Momentum_Position"] * data["Open_to_Open_Return"]
    )

    data["Momentum_Cumulative_Return"] = (
        (1 + data["Momentum_Strategy_Return"].fillna(0) / 100).cumprod() - 1
    ) * 100

    # Buy and Hold Returns
    data["Buy_Hold_Return"] = data["Open_to_Open_Return"]

    data["Buy_Hold_Cumulative"] = (
        (1 + data["Buy_Hold_Return"].fillna(0) / 100).cumprod() - 1
    ) * 100

    # Mean Reversion Maximum Drawdown
    mr_equity = 1 + data["MR_Cumulative_Return"] / 100
    mr_running_peak = mr_equity.cummax().clip(lower=1)

    mr_drawdown = (
        (mr_equity / mr_running_peak) - 1
    ) * 100

    max_drawdown = mr_drawdown.min()

    # Momentum Maximum Drawdown
    momentum_equity = 1 + data["Momentum_Cumulative_Return"] / 100
    momentum_running_peak = momentum_equity.cummax().clip(lower=1)

    momentum_drawdown = (
        (momentum_equity / momentum_running_peak) - 1
    ) * 100

    momentum_max_drawdown = momentum_drawdown.min()

   

    # Performance Summary
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #172235, #1E293B);
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 4px solid #10B981;
        margin: 25px 0 20px 0;
    ">
        <h2 style="color: #34D399; margin: 0;">
            📊 Performance Summary
        </h2>
        <p style="color: #94A3B8; margin: 5px 0 0 0;">
            Overall returns compared across three investment approaches
        </p>
    </div>
    """, unsafe_allow_html=True)

    mr_return = data["MR_Cumulative_Return"].iloc[-1]
    momentum_return = data["Momentum_Cumulative_Return"].iloc[-1]
    buy_hold_return = data["Buy_Hold_Cumulative"].iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Mean Reversion", f"{mr_return:.2f}%")

    with col2:
        st.metric("Momentum", f"{momentum_return:.2f}%")

    with col3:
        st.metric("Buy and Hold", f"{buy_hold_return:.2f}%")


    # Mean Reversion Statistics
    st.subheader("Mean Reversion Statistics")

    col1, col2, col3 = st.columns(3)

    col1.metric("Completed Trades", mr_total_trades)
    col2.metric("Win Rate", f"{win_rate:.2f}%")
    col3.metric("Average Trade Return", f"{avg_trade_return:.2f}%")

    st.metric("Maximum Drawdown", f"{max_drawdown:.2f}%")

    # Momentum Statistics
    st.subheader("Momentum Statistics")

    col1, col2, col3 = st.columns(3)

    col1.metric("Completed Trades", momentum_total_trades)
    col2.metric("Win Rate", f"{momentum_win_rate:.2f}%")
    col3.metric(
        "Average Trade Return",
        f"{momentum_avg_trade_return:.2f}%"
    )

    st.metric("Maximum Drawdown", f"{momentum_max_drawdown:.2f}%")

    # Mean Reversion Trade Log
    st.subheader("Mean Reversion Trade Log")
    st.dataframe(trade_log)

    # Momentum Trade Log
    st.subheader("Momentum Trade Log")
    st.dataframe(momentum_trade_log)

    # Display Historical Data
    st.subheader("Historical Data")
    st.dataframe(data)

    # Mean Reversion Entry Signals
    st.subheader("Mean Reversion Entry Signals")

    st.dataframe(
        data.loc[data["MR_Entry_Signal"], ["Close", "MA_20"]]
    )

    
    # Closing Price vs Moving Average Chart
    fig, ax = plt.subplots(figsize=(12, 5))

    fig.patch.set_facecolor("#101827")
    ax.set_facecolor("#172235")

    ax.plot(
        data.index, data["Close"],
        label="Closing Price",
        color="#34D399",
        linewidth=2.2
    )

    ax.plot(
        data.index, data["MA_20"],
        label="20-Week MA",
        color="#60A5FA",
        linewidth=1.8,
        linestyle="--"
    )

    ax.set_title(
        f"{ticker} - Closing Price vs Moving Average",
        color="#F8FAFC",
        fontsize=14,
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel("Date", color="#CBD5E1")
    ax.set_ylabel("Price (INR)", color="#CBD5E1")

    ax.tick_params(colors="#CBD5E1")
    ax.grid(True, color="#334155", alpha=0.5)

    ax.legend(
        facecolor="#1E293B",
        edgecolor="#334155",
        labelcolor="#F1F5F9"
    )

    for spine in ax.spines.values():
        spine.set_color("#334155")

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    
    # Wilder RSI Chart
    st.subheader("Relative Strength Index")

    st.write("Latest Wilder RSI:", round(data["Wilder_RSI"].iloc[-1], 2))

    fig_rsi, ax_rsi = plt.subplots(figsize=(12, 5))

    fig_rsi.patch.set_facecolor("#101827")
    ax_rsi.set_facecolor("#172235")

    ax_rsi.plot(
        data.index,
        data["Wilder_RSI"],
        label="14-Week Wilder RSI",
        color="#A78BFA",
        linewidth=2.2
    )

    ax_rsi.axhline(
        70, color="#F87171",
        linestyle="--", linewidth=1.5,
        label="Overbought (70)"
    )

    ax_rsi.axhline(
        30, color="#34D399",
        linestyle="--", linewidth=1.5,
        label="Oversold (30)"
    )

    ax_rsi.fill_between(
        data.index, 30, 70,
        color="#334155", alpha=0.15
    )

    ax_rsi.set_title(
        f"{ticker} - Wilder RSI",
        color="#F8FAFC",
        fontsize=14,
        fontweight="bold",
        pad=15
    )

    ax_rsi.set_xlabel("Date", color="#CBD5E1")
    ax_rsi.set_ylabel("RSI", color="#CBD5E1")
    ax_rsi.set_ylim(0, 100)

    ax_rsi.tick_params(colors="#CBD5E1")
    ax_rsi.grid(True, color="#334155", alpha=0.5)

    ax_rsi.legend(
        facecolor="#1E293B",
        edgecolor="#334155",
        labelcolor="#F1F5F9"
    )

    for spine in ax_rsi.spines.values():
        spine.set_color("#334155")

    fig_rsi.tight_layout()
    st.pyplot(fig_rsi)
    plt.close(fig_rsi)


   
    # Strategy Performance Comparison
    st.subheader("Strategy Performance Comparison")

    fig_returns, ax_returns = plt.subplots(figsize=(12, 5))

    fig_returns.patch.set_facecolor("#101827")
    ax_returns.set_facecolor("#172235")

    ax_returns.plot(
        data.index,
        data["MR_Cumulative_Return"],
        label="Mean Reversion",
        color="#34D399",
        linewidth=2.2
    )

    ax_returns.plot(
        data.index,
        data["Momentum_Cumulative_Return"],
        label="Momentum",
        color="#60A5FA",
        linewidth=2.2
    )

    ax_returns.plot(
        data.index,
        data["Buy_Hold_Cumulative"],
        label="Buy and Hold",
        color="#FBBF24",
        linewidth=2.2
    )

    ax_returns.axhline(
        0,
        color="#94A3B8",
        linestyle=":",
        linewidth=1
    )

    ax_returns.set_title(
        f"{ticker} - Strategy Performance Comparison",
        color="#F8FAFC",
        fontsize=14,
        fontweight="bold",
        pad=15
    )

    ax_returns.set_xlabel("Date", color="#CBD5E1")
    ax_returns.set_ylabel("Cumulative Return (%)", color="#CBD5E1")

    ax_returns.tick_params(colors="#CBD5E1")
    ax_returns.grid(True, color="#334155", alpha=0.5)

    ax_returns.legend(
        facecolor="#1E293B",
        edgecolor="#334155",
        labelcolor="#F1F5F9"
    )

    for spine in ax_returns.spines.values():
        spine.set_color("#334155")

    fig_returns.tight_layout()
    st.pyplot(fig_returns)
    plt.close(fig_returns)


else:
    st.error("No data found. Please check the stock symbol.")