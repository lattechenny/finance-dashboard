import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="金融看板", layout="wide")
st.title("股价走势对比")

TICKERS = ["ETN", "NVDA", "SPY"]
end = datetime.today()
start = end - timedelta(days=365)

def fetch_single(ticker, start, end, retries=3, delay=2):
    """逐只抓取，失败后指数退避重试。"""
    for attempt in range(retries):
        try:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
            if df.empty:
                raise ValueError(f"{ticker} 返回空数据")
            close = df["Close"]
            # yfinance 某些版本返回 DataFrame，取第一列
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            close.name = ticker
            return close
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                st.warning(f"无法获取 {ticker} 的数据：{e}")
                return None

@st.cache_data(ttl=3600)
def load_data(tickers, start, end):
    series = {}
    for t in tickers:
        s = fetch_single(t, start, end)
        if s is not None:
            series[t] = s
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series)

with st.spinner("加载数据中..."):
    df = load_data(TICKERS, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

if df.empty:
    st.error("所有股票数据获取失败，请检查网络或稍后重试。")
    st.stop()

missing = [t for t in TICKERS if t not in df.columns]
if missing:
    st.warning(f"以下股票数据未能加载：{', '.join(missing)}")

# 归一化为百分比涨跌（以起始价格为基准）
df_norm = (df / df.iloc[0] - 1) * 100

fig = go.Figure()
colors = {"ETN": "#00C4FF", "NVDA": "#76B900", "SPY": "#FF6B35"}

for ticker in df.columns:
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
    "区间涨跌幅": df_norm.iloc[-1].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"),
    "区间最高价 ($)": df.max().round(2),
    "区间最低价 ($)": df.min().round(2),
})
st.dataframe(stats, use_container_width=True)
