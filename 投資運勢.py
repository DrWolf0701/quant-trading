"""
🎯 投資運勢 app
結合真實市場數據 + 趣味占卜
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import random
from datetime import datetime

# 頁面設定
st.set_page_config(page_title="🎯 投資運勢", page_title="小熊投資運勢")

st.title("🎯 小熊投資運勢")
st.markdown("---")

# 側邊欄 - 輸入
with st.sidebar:
    st.header("🎈 輸入你的資料")
    name = st.text_input("你的名字", value="投資人")
    birthday = st.date_input("生日", min_value=datetime(1950,1,1))
    
    st.markdown("---")
    st.markdown("### 📊 數據來源")
    st.info("結合真實市場數據給出建議")

# 獲取市場數據
@st.cache_data
def get_market_data():
    """獲取大盤數據"""
    data = {}
    
    # S&P 500
    try:
        spy = yf.download("SPY", period="3mo", progress=False, timeout=10)
        close = spy['Close']
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        data['sp500'] = {
            'close': close.iloc[-1],
            'sma20': sma20,
            'sma50': sma50,
            'rsi': rsi,
            'trend': '多頭' if sma20 > sma50 else '空頭'
        }
    except:
        data['sp500'] = {'trend': '震盪', 'rsi': 50}
    
    # VIX
    try:
        vix = yf.download("^VIX", period="5d", progress=False, timeout=10)
        vix_close = vix['Close']
        if isinstance(vix_close, pd.DataFrame):
            vix_close = vix_close.iloc[:, 0]
        data['vix'] = vix_close.iloc[-1]
    except:
        data['vix'] = 15
    
    # 板塊
    sectors = {
        'XLK': '科技',
        'XLF': '金融',
        'XLE': '能源',
        'XLV': '醫療',
        'XLY': '消費'
    }
    
    sector_returns = []
    for ticker, name in sectors.items():
        try:
            sector = yf.download(ticker, period="1mo", progress=False, timeout=10)
            close = sector['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
            sector_returns.append((name, ret))
        except:
            sector_returns.append((name, 0))
    
    sector_returns.sort(key=lambda x: x[1], reverse=True)
    data['top_sector'] = sector_returns[0][0] if sector_returns else '科技'
    
    return data

# 計算運勢
def calculate_fortune(name, birthday, market_data):
    """計算投資運勢"""
    
    # 幸運數字（基於生日）
    seed = birthday.year * 10000 + birthday.month * 100 + birthday.day
    random.seed(seed)
    lucky_numbers = sorted(random.sample(range(1, 100), 3))
    
    # 幸運股票（基於名字）
    stock_list = ['AAPL', 'NVDA', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'BRK-B', 'AMD', 'INTC']
    random.seed(hash(name))
    lucky_stock = random.choice(stock_list)
    
    # 幸運板塊
    lucky_sectors = ['科技', '金融', '能源', '醫療', '消費']
    random.seed(seed + 1)
    lucky_sector = random.choice(lucky_sectors)
    
    # 運勢等級（基於市場數據 + 隨機）
    sp = market_data.get('sp500', {})
    trend = sp.get('trend', '震盪')
    rsi = sp.get('rsi', 50)
    vix = market_data.get('vix', 15)
    
    # 根據數據調整運勢
    base_stars = 3
    
    if trend == '多頭' and rsi < 70 and vix < 20:
        base_stars = 4
    if trend == '多頭' and rsi < 50 and vix < 15:
        base_stars = 5
    if trend == '空頭' or rsi > 70 or vix > 25:
        base_stars = 2
    
    # 隨機浮動
    stars = max(1, min(5, base_stars + random.randint(-1, 1)))
    
    # 趨勢建議
    if rsi > 70:
        trend_advice = "市場過熱，留意回檔風險"
        action = "分批賣出"
    elif rsi < 30:
        if trend == '多頭':
            trend_advice = "超跌反彈有望"
            action = "分批買入"
        else:
            trend_advice = "謹慎為宜"
            action = "觀望"
    elif trend == '多頭':
        trend_advice = "多頭趨勢持續"
        action = "持股待漲"
    elif trend == '空頭':
        trend_advice = "空頭趨勢延續"
        action = "觀望為主"
    else:
        trend_advice = "市場震盪整理"
        action = "區間操作"
    
    # VIX 建議
    if vix > 25:
        vix_advice = "波動大，謹慎操作"
    elif vix < 15:
        vix_advice = "市場冷靜，可適度積極"
    else:
        vix_advice = "正常波動範圍"
    
    return {
        'stars': stars,
        'lucky_numbers': lucky_numbers,
        'lucky_stock': lucky_stock,
        'lucky_sector': lucky_sector,
        'trend': trend,
        'trend_advice': trend_advice,
        'action': action,
        'rsi': rsi,
        'vix': vix,
        'vix_advice': vix_advice,
        'top_sector': market_data.get('top_sector', '科技')
    }

# 顯示結果
if st.button("🔮 開始占卜", type="primary"):
    with st.spinner("正在結合市場數據..."):
        market_data = get_market_data()
        fortune = calculate_fortune(name, birthday, market_data)
        
        st.markdown("---")
        
        # 運勢等級
        stars_str = "⭐" * fortune['stars'] + "☆" * (5 - fortune['stars'])
        st.markdown(f"## 🌟 {name} 的投資運勢")
        st.markdown(f"### {stars_str}")
        
        # 幸運資訊
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 幸運股票", fortune['lucky_stock'])
        
        with col2:
            st.metric("🎯 幸運數字", str(fortune['lucky_numbers']))
        
        with col3:
            st.metric("🏭 幸運板塊", fortune['lucky_sector'])
        
        st.markdown("---")
        
        # 市場數據
        st.markdown("### 📈 市場數據")
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("S&P 500 趨勢", fortune['trend'])
        with m2:
            st.metric("RSI", f"{fortune['rsi']:.1f}")
        with m3:
            st.metric("VIX 恐慌指數", f"{fortune['vix']:.1f}")
        with m4:
            st.metric("最強板塊", fortune['top_sector'])
        
        st.markdown("---")
        
        # 建議
        st.markdown("### 💡 小熊建議")
        
        st.success(f"**趨勢分析：** {fortune['trend_advice']}")
        st.warning(f"**VIX 建議：** {fortune['vix_advice']}")
        
        st.markdown(f"### 🎯 今日宜：{fortune['action']}")
        
        st.markdown("---")
        
        # 小熊語
        quotes = [
            "股市有風險，占卜僅供參考！",
            "運勢好也要做好風險管理！",
            "學習是最好的投資！",
            "保持耐心，等待機會！",
            "分散風險，不要把雞蛋放同一個籃子！"
        ]
        st.info(f"🐻 小熊語：{random.choice(quotes)}")

# 說明
st.markdown("---")
st.caption("⚠️ 本 app 僅供娛樂用途，不構成投資建議。投資有風險，請自行評估。")
