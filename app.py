import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="金融看板", layout="wide")
st.title("股价走势对比")

TICKERS = ["ETN", "NVDA", "SPY"]
end = datetime.today()
start = end - timedelta(days=365)

@st.cache_data(ttl=3600)
def load_data(tickers, start, end):
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)["Close"]
    return data

with st.spinner("加载数据中..."):
    df = load_data(TICKERS, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

# 归一化为百分比涨跌（以起始价格为基准）
df_norm = (df / df.iloc[0] - 1) * 100

fig = go.Figure()
colors = {"ETN": "#00C4FF", "NVDA": "#76B900", "SPY": "#FF6B35"}

for ticker in TICKERS:
    fig.add_trace(go.Scatter(
        x=df_norm.index,
        y=df_norm[ticker],
        name=ticker,
        line=dict(color=colors[ticker], width=2),
        hovertemplate=f"<b>{ticker}</b><br>日期: %{{x|%Y-%m-%d}}<br>涨跌: %{{y:.2f}}%<extra></extra>"
    ))

fig.update_layout(
    title=f"过去一年涨跌幅对比（基准: {start.strftime('%Y-%m-%d')}）",
    xaxis_title="日期",
    yaxis_title="涨跌幅 (%)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
    font=dict(color="white"),
    xaxis=dict(gridcolor="#2a2a2a"),
    yaxis=dict(gridcolor="#2a2a2a", ticksuffix="%"),
)

st.plotly_chart(fig, use_container_width=True)

# 简单统计表
st.subheader("区间统计")
stats = pd.DataFrame({
    "最新价 ($)": df.iloc[-1].round(2),
    "区间涨跌幅": df_norm.iloc[-1].map("{:.2f}%".format),
    "区间最高价 ($)": df.max().round(2),
    "区间最低价 ($)": df.min().round(2),
})
st.dataframe(stats, use_container_width=True)
