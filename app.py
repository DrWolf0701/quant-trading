"""
小熊美股投資 - 導航頁面
多頁面應用
"""

import streamlit as st

# 頁面設定
st.set_page_config(
    page_title="小熊美股投資",
    page_icon="🐻",
    layout="wide"
)

st.title("🐻 小熊美股投資")
st.markdown("---")

# 側邊欄導航
st.sidebar.title("📊 導航選單")

# 選擇頁面
page = st.sidebar.radio(
    "選擇功能",
    ["🤖 AI選股", "📈 量化交易", "⚡ 日內交易", "🎯 投資運勢"]
)

# 根據選擇顯示不同頁面
if page == "🤖 AI選股":
    # AI 選股頁面
    st.header("🤖 AI選股")
    st.info("正在載入 AI 選股工具...")
    
    # 引入需要的庫
    import yfinance as yf
    import pandas as pd
    import numpy as np
    
    # 股票清單
    quick_stocks = {
        "科技": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA"],
        "金融": ["JPM", "BAC", "GS", "V", "MA"],
        "ETF": ["SPY", "QQQ", "VOO", "VTI", "ARKK"],
        "晶片": ["AMD", "INTC", "NVDA", "TSM", "AVGO"],
        "我們追蹤": ["BRK-B", "BRKU", "RKLB", "DJCO", "GGR", "BYDDY"],
    }
    
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_category = st.selectbox("類別", list(quick_stocks.keys()), key="category")
    with col2:
        ticker = st.selectbox("股票", quick_stocks[selected_category], key="stock")
    
    if ticker:
        with st.spinner(f"正在分析 {ticker}..."):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                st.header(f"📈 {info.get('shortName', ticker)} ({ticker})")
                
                # 股價
                col1, col2, col3, col4 = st.columns(4)
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                previous_close = info.get('previousClose', 0)
                price_change = current_price - previous_close
                price_change_pct = (price_change / previous_close * 100) if previous_close else 0
                
                with col1:
                    st.metric("價格", f"${current_price:.2f}", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
                with col2:
                    market_cap = info.get('marketCap', 0)
                    st.metric("市值", f"${market_cap / 1e12:.2f}T" if market_cap else "N/A")
                with col3:
                    pe = info.get('trailingPE', 0)
                    st.metric("P/E", f"{pe:.2f}" if pe else "N/A")
                with col4:
                    vol = info.get('volume', 0)
                    st.metric("成交量", f"{vol / 1e6:.1f}M")
                
                # 新聞
                st.subheader("📰 新聞")
                try:
                    news = stock.news
                    if news:
                        for n in news[:5]:
                            title = n.get('content', {}).get('title', 'No title')
                            link = n.get('content', {}).get('canonicalUrl', {}).get('url', '')
                            if title and title != 'No title':
                                st.markdown(f"- [{title}]({link})")
                    else:
                        st.info("暫無新聞")
                except:
                    st.info("暫無新聞")
                    
            except Exception as e:
                st.error(f"無法取得數據: {e}")

elif page == "📈 量化交易":
    exec(open("_量化交易系統.py").read())
elif page == "⚡ 日內交易":
    exec(open("_日內交易系統.py").read())
elif page == "🎯 投資運勢":
    exec(open("_投資運勢.py").read())
