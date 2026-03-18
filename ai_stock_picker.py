"""
🤖 AI 選股工具 - Streamlit App
AI Stock Picker - Real-time Data
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 頁面設定
st.set_page_config(
    page_title="AI 選股工具",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI 選股工具")
st.markdown("---")

# 側邊欄
with st.sidebar:
    st.header("📊 功能")
    st.info("輸入股票代碼，獲取即時分析")
    st.markdown("---")
    st.markdown("**支援市場：**")
    st.markdown("- 美股：AAPL, MSFT, GOOGL...")
    st.markdown("- ETF：SPY, QQQ, VOO...")
    st.markdown("- 熱門股票快速選擇")

# 熱門股票快捷選擇
st.subheader("⚡ 快速選擇")

quick_stocks = {
    "科技": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA"],
    "金融": ["JPM", "BAC", "GS", "V", "MA"],
    "ETF": ["SPY", "QQQ", "VOO", "VTI", "ARKK"],
    "晶片": ["AMD", "INTC", "NVDA", "TSM", "AVGO"],
    "我們追蹤": ["BRK-B", "BRKU", "RKLB", "DJCO", "GGR", "BYDDY"],
}

# 選擇股票
col1, col2 = st.columns([1, 2])
with col1:
    selected_category = st.selectbox("類別", list(quick_stocks.keys()), key="category")

with col2:
    ticker = st.selectbox("股票", quick_stocks[selected_category], key="stock")

# 自動分析
if ticker:
    with st.spinner(f"正在分析 {ticker}..."):
        try:
            # 獲取股票數據
            stock = yf.Ticker(ticker)
            
            # 獲取即時價格
            info = stock.info
            
            # 顯示基本資料
            st.header(f"📈 {info.get('shortName', ticker)} ({ticker})")
            
            # 股價資訊
            col1, col2, col3, col4 = st.columns(4)
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            previous_close = info.get('previousClose', 0)
            price_change = current_price - previous_close
            price_change_pct = (price_change / previous_close * 100) if previous_close else 0
            
            with col1:
                st.metric("當前價格", f"${current_price:.2f}", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
            with col2:
                st.metric("市值", f"${info.get('marketCap', 0) / 1e12:.2f}T" if info.get('marketCap') else "N/A")
            with col3:
                st.metric("52週高低", f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}")
            with col4:
                st.metric("成交量", f"{info.get('volume', 0) / 1e6:.1f}M")
            
            st.markdown("---")
            
            # 基本面分析
            st.subheader("📊 基本面數據")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pe_ratio = info.get('trailingPE', 0)
                st.metric("本益比 (P/E)", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
            
            with col2:
                dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                st.metric("殖利率", f"{dividend_yield:.2f}%" if dividend_yield else "N/A")
            
            with col3:
                roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                st.metric("ROE", f"{roe:.2f}%" if roe else "N/A")
            
            with col4:
                debt_to_equity = info.get('debtToEquity', 0)
                st.metric("負債比", f"{debt_to_equity:.2f}%" if debt_to_equity else "N/A")
            
            # 更多基本面
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("EPS", f"${info.get('trailingEps', 0):.2f}" if info.get('trailingEps') else "N/A")
            
            with col2:
                st.metric("營收", f"${info.get('totalRevenue', 0) / 1e9:.2f}B" if info.get('totalRevenue') else "N/A")
            
            with col3:
                st.metric("營收成長", f"{info.get('revenueGrowth', 0) * 100:.2f}%" if info.get('revenueGrowth') else "N/A")
            
            with col4:
                st.metric("beta", f"{info.get('beta', 0):.2f}" if info.get('beta') else "N/A")
            
            st.markdown("---")
            
            # 近期新聞
            st.subheader("📰 近期新聞")
            
            # 嘗試獲取新聞
            try:
                news = stock.news
                if news:
                    for i, n in enumerate(news[:5]):
                        # 標題在 content 裡面
                        title = n.get('content', {}).get('title', 'No title')
                        provider = n.get('content', {}).get('provider', {}).get('displayName', 'Unknown')
                        link = n.get('content', {}).get('canonicalUrl', {}).get('url', '')
                        
                        with st.expander(f"📰 {title[:60]}..."):
                            st.markdown(f"**{title}**")
                            st.markdown(f"來源: {provider}")
                            if link:
                                st.markdown(f"[閱讀更多]({link})")
                else:
                    st.info("暫無新聞數據")
            except:
                st.info("暫無新聞數據")
            
            st.markdown("---")
            
            # AI 建議
            st.subheader("🤖 AI 分析建議")
            
            # 簡單的 AI 邏輯判斷
            signals = []
            
            if pe_ratio and pe_ratio < 20:
                signals.append("✅ 本益比偏低 (可能被低估)")
            elif pe_ratio and pe_ratio > 40:
                signals.append("⚠️ 本益比偏高")
            
            if dividend_yield > 3:
                signals.append("✅ 殖利率不錯 (>3%)")
            
            if roe > 15:
                signals.append("✅ ROE 表現優異 (>15%)")
            elif roe and roe < 5:
                signals.append("⚠️ ROE 偏低")
            
            if price_change_pct > 5:
                signals.append("⚠️ 單日漲幅過大")
            elif price_change_pct < -5:
                signals.append("⚠️ 單日跌幅過大")
            
            if info.get('volume', 0) > 50e6:
                signals.append("✅ 成交量活躍")
            
            # 顯示訊號
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.write("**技術訊號：**")
                for signal in signals:
                    st.write(f"- {signal}")
                if not signals:
                    st.write("- 暫無明確訊號")
            
            with col2:
                # 簡單的建議
                buy_signals = sum(1 for s in signals if "✅" in s)
                warning_signals = sum(1 for s in signals if "⚠️" in s)
                
                if buy_signals > warning_signals and buy_signals >= 2:
                    recommendation = "📈 建議關注"
                    color = "green"
                elif warning_signals > buy_signals:
                    recommendation = "📉 建議觀望"
                    color = "red"
                else:
                    recommendation = "⏳ 中性"
                    color = "gray"
                
                st.markdown(f":{color}[**{recommendation}**]")
                st.caption("※ 此為機器人自動分析，不構成投資建議")
            
            st.markdown("---")
            
            # 股價走勢圖
            st.subheader("📈 股價走勢")
            
            # 取得歷史數據
            hist = stock.history(period="1mo")
            
            if not hist.empty:
                # 簡單的 K 線圖
                chart_data = pd.DataFrame({
                    'Date': hist.index,
                    'Open': hist['Open'],
                    'High': hist['High'],
                    'Low': hist['Low'],
                    'Close': hist['Close'],
                    'Volume': hist['Volume']
                })
                
                st.line_chart(hist['Close'], use_container_width=True)
                
                # 顯示近期資料
                st.subheader("📋 近期價格")
                st.dataframe(hist.tail(10), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ 無法獲取 {ticker} 的數據: {str(e)}")
            st.info("請檢查股票代碼是否正確")

# 頁腳
st.markdown("---")
st.caption("🤖 AI 選股工具 v1.0 | 數據來源: Yahoo Finance | 僅供參考，不構成投資建議")
