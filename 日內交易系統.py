"""
日內交易策略量化系統
Day Trading Quantitative System
更新時間：2026-03-12

策略：
1. 突破策略 (Breakout) - 突破區間高點買入
2. 反轉策略 (Reversal) - RSI超賣時買入
3. 區間策略 (Range) - 支撐買入、壓力賣出
4. 均線策略 (MA Crossover) - 短均線穿越長均線
5. Gap and Go - 跳空缺口後順勢交易
6. 動能交易 (Momentum) - 強勢股順勢追蹤
7. VWAP 回歸 (VWAP Regression) - 價格回歸 VWAP
8. 開盤區間突破 (Opening Range) - 開盤後突破區間進場
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="📊 日內交易系統", layout="wide")
st.title("📊 日內交易量化系統")

# 側邊欄 - 參數設定
with st.sidebar:
    st.header("⚙️ 參數設定")
    
    symbol = st.text_input("股票代碼", value="AAPL")
    
    strategy = st.selectbox(
        "交易策略",
        ["突破策略 (Breakout)", "反轉策略 (Reversal)", "區間策略 (Range)", "均線策略 (MA Crossover)", 
         "Gap and Go", "動能交易 (Momentum)", "VWAP 回歸", "開盤區間突破"]
    )
    
    st.markdown("---")
    st.subheader("📈 策略參數")
    
    if strategy == "突破策略 (Breakout)":
        lookback = st.slider("回顧週期", 5, 60, 20)
        volume_mult = st.slider("成交量倍數", 1.0, 3.0, 1.5)
    
    elif strategy == "反轉策略 (Reversal)":
        rsi_oversold = st.slider("RSI超賣門檻", 10, 40, 30)
        rsi_overbought = st.slider("RSI超買門檻", 60, 90, 70)
    
    elif strategy == "區間策略 (Range)":
        range_period = st.slider("區間週期", 10, 60, 20)
    
    elif strategy == "Gap and Go":
        gap_threshold = st.slider("跳空缺口門檻 (%)", 0.5, 5.0, 1.0)
        volume_requirement = st.slider("成交量要求 (倍)", 1.0, 3.0, 1.5)
    
    elif strategy == "動能交易 (Momentum)":
        momentum_period = st.slider("動能週期", 5, 30, 14)
        momentum_threshold = st.slider("動能門檻", 0.5, 5.0, 2.0)
    
    elif strategy == "VWAP 回歸":
        vwap_tolerance = st.slider("VWAP 偏離容差 (%)", 0.1, 2.0, 0.5)
    
    elif strategy == "開盤區間突破":
        opening_range_min = st.slider("開盤區間分鐘", 5, 30, 15)
        breakout_threshold = st.slider("突破門檻 (%)", 0.2, 2.0, 0.5)
    
    else:  # 均線策略
        fast_ma = st.slider("快速均線", 5, 30, 10)
        slow_ma = st.slider("慢速均線", 20, 100, 50)
    
    initial_capital = st.number_input("初始資金 ($)", value=10000)
    position_size = st.slider("倉位比例 (%)", 10, 100, 50)

# 模擬數據生成函數
def generate_mock_data(symbol, period="5d", interval="5m"):
    """生成模擬數據（當真實數據獲取失敗時使用）"""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # 根據股票代碼生成不同的基準價格
    base_prices = {
        "AAPL": 175, "GOOGL": 140, "MSFT": 370, "AMZN": 178, 
        "TSLA": 245, "NVDA": 480, "META": 380, "BRK-B": 500,
        "RKLB": 18, "DJCO": 520, "GGR": 4.5, "BYDDY": 12
    }
    base_price = base_prices.get(symbol.upper(), 100)
    
    # 產生時間序列
    now = datetime.now()
    if interval == "5m":
        freq = "5T"
        periods = 390 * 5  # 5天 x 每天390個5分鐘
    else:
        freq = "15T"
        periods = 130 * 5
    
    dates = pd.date_range(end=now, periods=periods, freq=freq)
    
    # 隨機漫步生成價格
    np.random.seed(hash(symbol) % 10000)
    returns = np.random.normal(0.0001, 0.002, periods)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 生成 OHLCV 數據
    df = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.002, 0.002, periods)),
        'High': prices * (1 + np.random.uniform(0.001, 0.005, periods)),
        'Low': prices * (1 + np.random.uniform(-0.005, -0.001, periods)),
        'Close': prices,
        'Volume': np.random.randint(100000, 5000000, periods)
    }, index=dates)
    
    df.index.name = 'Datetime'
    return df

# 獲取數據（使用直接 HTTP API）
@st.cache_data
def get_intraday_data(symbol, period="5d", interval="5m"):
    """獲取日內數據（直接 HTTP API + 模擬數據備援）"""
    import requests
    import time
    
    # 計算時間範圍
    now = pd.Timestamp.now()
    if period == "5d":
        start = now - pd.Timedelta(days=7)
    elif period == "1mo":
        start = now - pd.Timedelta(days=35)
    else:
        start = now - pd.Timedelta(days=7)
    
    # Yahoo Finance API
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "period1": int(start.timestamp()),
        "period2": int(now.timestamp()),
        "interval": interval
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            
            df = pd.DataFrame({
                'Open': quotes['open'],
                'High': quotes['high'],
                'Low': quotes['low'],
                'Close': quotes['close'],
                'Volume': quotes['volume']
            }, index=pd.to_datetime(timestamps, unit='s'))
            
            df = df.dropna()
            
            if len(df) > 10:
                st.success(f"✅ 顯示 {symbol} 真實數據")
                return df
        
        # 如果 API 失敗，使用模擬數據
        st.warning(f"⚠️ 無法獲取 {symbol} 真實數據，使用模擬數據展示功能")
        return generate_mock_data(symbol, period, interval)
        
    except Exception as e:
        st.warning(f"⚠️ 獲取數據失敗，使用模擬數據展示功能: {e}")
        return generate_mock_data(symbol, period, interval)

# 計算技術指標
def calculate_indicators(df):
    """計算技術指標"""
    df = df.copy()
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 均線
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    
    # 支撐/壓力
    df['High_20'] = df['High'].rolling(20).max()
    df['Low_20'] = df['Low'].rolling(20).min()
    
    # 成交量均線
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    
    return df

# 突破策略訊號
def breakout_signals(df, lookback=20, volume_mult=1.5):
    """突破策略訊號"""
    df = df.copy()
    df['High_lookback'] = df['High'].rolling(lookback).max()
    df['Volume_MA'] = df['Volume'].rolling(lookback).mean()
    
    # 買入訊號：價格突破新高 + 成交量放大
    df['Buy_Signal'] = (df['Close'] > df['High_lookback'].shift(1)) & \
                       (df['Volume'] > df['Volume_MA'] * volume_mult)
    
    # 賣出訊號：價格跌破前低
    df['Low_lookback'] = df['Low'].rolling(lookback).min()
    df['Sell_Signal'] = df['Close'] < df['Low_lookback'].shift(1)
    
    return df

# 反轉策略訊號
def reversal_signals(df, rsi_oversold=30, rsi_overbought=70):
    """反轉策略訊號"""
    df = df.copy()
    
    # 買入訊號：RSI超賣後回升
    df['Buy_Signal'] = (df['RSI'] < rsi_oversold) & (df['RSI'].shift(1) < df['RSI'])
    
    # 賣出訊號：RSI超買後回落
    df['Sell_Signal'] = (df['RSI'] > rsi_overbought) & (df['RSI'].shift(1) > df['RSI'])
    
    return df

# 區間策略訊號
def range_signals(df, period=20):
    """區間策略訊號"""
    df = df.copy()
    df['Range_High'] = df['High'].rolling(period).max()
    df['Range_Low'] = df['Low'].rolling(period).min()
    
    # 買入訊號：接近支撐
    df['Buy_Signal'] = df['Close'] <= df['Range_Low'] * 1.01
    
    # 賣出訊號：接近壓力
    df['Sell_Signal'] = df['Close'] >= df['Range_High'] * 0.99
    
    return df

# 均線策略訊號
def ma_crossover_signals(df, fast=10, slow=50):
    """均線交叉策略訊號"""
    df = df.copy()
    df['MA_Fast'] = df['Close'].rolling(fast).mean()
    df['MA_Slow'] = df['Close'].rolling(slow).mean()
    
    # 買入訊號：快線穿越慢線
    df['Buy_Signal'] = (df['MA_Fast'] > df['MA_Slow']) & \
                       (df['MA_Fast'].shift(1) <= df['MA_Slow'].shift(1))
    
    # 賣出訊號：快線跌破慢線
    df['Sell_Signal'] = (df['MA_Fast'] < df['MA_Slow']) & \
                        (df['MA_Fast'].shift(1) >= df['MA_Slow'].shift(1))
    
    return df

# Gap and Go 策略訊號
def gap_and_go_signals(df, gap_threshold=1.0, volume_mult=1.5):
    """Gap and Go 策略 - 跳空缺口後順勢交易"""
    df = df.copy()
    
    # 計算開盤跳空
    df['Prev_Close'] = df['Close'].shift(1)
    df['Gap'] = ((df['Open'] - df['Prev_Close']) / df['Prev_Close']) * 100
    
    # 成交量放大
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    
    # 買入訊號：向上跳空且成交量放大
    df['Buy_Signal'] = (df['Gap'] > gap_threshold) & (df['Volume'] > df['Volume_MA'] * volume_mult)
    
    # 賣出訊號：收盤跌破開盤
    df['Sell_Signal'] = df['Close'] < df['Open']
    
    return df

# 動能交易策略訊號
def momentum_signals(df, period=14, threshold=2.0):
    """動能交易策略 - 順勢追蹤"""
    df = df.copy()
    
    # 計算動能
    df['Momentum'] = df['Close'] - df['Close'].shift(period)
    df['Momentum_Pct'] = (df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period) * 100
    
    # 買入訊號：動能強勁向上
    df['Buy_Signal'] = df['Momentum_Pct'] > threshold
    
    # 賣出訊號：動能反轉向下
    df['Sell_Signal'] = df['Momentum_Pct'] < -threshold
    
    return df

# VWAP 回歸策略訊號
def vwap_regression_signals(df, tolerance=0.5):
    """VWAP 回歸策略 - 價格回歸 VWAP"""
    df = df.copy()
    
    # 計算 VWAP
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (df['Typical_Price'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # 偏離度
    df['VWAP_Deviation'] = ((df['Close'] - df['VWAP']) / df['VWAP']) * 100
    
    # 買入訊號：價格低於 VWAP 後回升
    df['Buy_Signal'] = (df['VWAP_Deviation'] < -tolerance) & (df['VWAP_Deviation'] > df['VWAP_Deviation'].shift(1))
    
    # 賣出訊號：價格高於 VWAP 後回落
    df['Sell_Signal'] = (df['VWAP_Deviation'] > tolerance) & (df['VWAP_Deviation'] < df['VWAP_Deviation'].shift(1))
    
    return df

# 開盤區間突破策略訊號
def opening_range_signals(df, minutes=15, threshold=0.5):
    """開盤區間突破策略"""
    df = df.copy()
    
    # 計算開盤區間
    df['Open_Range_High'] = df['High'].rolling(minutes).max()
    df['Open_Range_Low'] = df['Low'].rolling(minutes).min()
    
    # 買入訊號：突破開盤區間高點
    df['Buy_Signal'] = (df['Close'] > df['Open_Range_High'].shift(1)) & \
                       ((df['Close'] - df['Open_Range_High'].shift(1)) / df['Open_Range_High'].shift(1) * 100 > threshold)
    
    # 賣出訊號：跌破開盤區間低點
    df['Sell_Signal'] = (df['Close'] < df['Open_Range_Low'].shift(1)) & \
                        ((df['Open_Range_Low'].shift(1) - df['Close']) / df['Open_Range_Low'].shift(1) * 100 > threshold)
    
    return df

# 回測函數
def backtest(df, strategy_name, initial_capital=10000, position_pct=0.5):
    """回測"""
    df = df.copy()
    
    # 初始化
    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    portfolio_values = []
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # 買入訊號
        if row.get('Buy_Signal', False) and position == 0:
            shares = int((capital * position_pct) / row['Close'])
            if shares > 0:
                cost = shares * row['Close']
                position = shares
                entry_price = row['Close']
                capital -= cost
                trades.append({
                    'time': row.name,
                    'type': 'BUY',
                    'price': row['Close'],
                    'shares': shares
                })
        
        # 賣出訊號
        elif row.get('Sell_Signal', False) and position > 0:
            proceeds = position * row['Close']
            profit = proceeds - (position * entry_price)
            capital += proceeds
            trades.append({
                'time': row.name,
                'type': 'SELL',
                'price': row['Close'],
                'shares': position,
                'profit': profit
            })
            position = 0
            entry_price = 0
        
        # 記錄投資組合價值
        portfolio_value = capital + (position * row['Close']) if position > 0 else capital
        portfolio_values.append(portfolio_value)
    
    # 最終結算
    if position > 0:
        final_price = df.iloc[-1]['Close']
        proceeds = position * final_price
        trades.append({
            'time': df.iloc[-1].name,
            'type': 'SELL',
            'price': final_price,
            'shares': position,
            'profit': proceeds - (position * entry_price)
        })
        capital = capital + proceeds
        position = 0
    
    # 計算統計
    total_return = (capital - initial_capital) / initial_capital * 100
    
    winning_trades = [t for t in trades if t.get('profit', 0) > 0]
    losing_trades = [t for t in trades if t.get('profit', 0) < 0]
    
    win_rate = len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0
    
    avg_win = np.mean([t['profit'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['profit'] for t in losing_trades]) if losing_trades else 0
    
    return {
        'final_capital': capital,
        'total_return': total_return,
        'trades': trades,
        'portfolio_values': portfolio_values,
        'win_rate': win_rate,
        'total_trades': len(trades),
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_drawdown': calculate_max_drawdown(portfolio_values) if portfolio_values else 0
    }

def calculate_max_drawdown(values):
    """計算最大回撤"""
    if not values:
        return 0
    peak = values[0]
    max_dd = 0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return max_dd

# 主程式
if st.button("🔄 執行回測", type="primary"):
    with st.spinner("正在獲取數據..."):
        df = get_intraday_data(symbol)
        
        if df is not None and len(df) > 0:
            # 計算指標
            df = calculate_indicators(df)
            
            # 選擇策略
            if strategy == "突破策略 (Breakout)":
                df = breakout_signals(df, lookback, volume_mult)
            elif strategy == "反轉策略 (Reversal)":
                df = reversal_signals(df, rsi_oversold, rsi_overbought)
            elif strategy == "區間策略 (Range)":
                df = range_signals(df, range_period)
            elif strategy == "Gap and Go":
                df = gap_and_go_signals(df, gap_threshold, volume_requirement)
            elif strategy == "動能交易 (Momentum)":
                df = momentum_signals(df, momentum_period, momentum_threshold)
            elif strategy == "VWAP 回歸":
                df = vwap_regression_signals(df, vwap_tolerance)
            elif strategy == "開盤區間突破":
                df = opening_range_signals(df, opening_range_min, breakout_threshold)
            else:
                df = ma_crossover_signals(df, fast_ma, slow_ma)
            
            # 執行回測
            results = backtest(df, strategy, initial_capital, position_size/100)
            
            # 顯示結果
            st.success("✅ 回測完成！")
            
            # 統計數據
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 最終資金", f"${results['final_capital']:,.2f}")
            col2.metric("📈 總報酬", f"{results['total_return']:.2f}%", 
                       delta=f"{results['total_return']:.2f}%")
            col3.metric("🎯 勝率", f"{results['win_rate']:.1f}%")
            col4.metric("📉 最大回撤", f"{results['max_drawdown']:.2f}%")
            
            col5, col6 = st.columns(2)
            col5.metric("總交易次數", results['total_trades'])
            col6.metric("平均獲利/虧損", f"${results['avg_win']:.2f} / ${results['avg_loss']:.2f}")
            
            # 繪製圖表
            st.subheader(f"📊 {symbol} 價格與交易訊號")
            
            fig = go.Figure()
            
            # K線
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='K線'
            ))
            
            # 買入訊號
            buy_signals = df[df['Buy_Signal'] == True]
            fig.add_trace(go.Scatter(
                x=buy_signals.index,
                y=buy_signals['Close'],
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='green'),
                name='買入訊號'
            ))
            
            # 賣出訊號
            sell_signals = df[df['Sell_Signal'] == True]
            fig.add_trace(go.Scatter(
                x=sell_signals.index,
                y=sell_signals['Close'],
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='red'),
                name='賣出訊號'
            ))
            
            # 均線
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='orange', width=1)))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], name='MA50', line=dict(color='blue', width=1)))
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 資金曲線
            if results['portfolio_values']:
                st.subheader("💵 資金曲線")
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    y=results['portfolio_values'],
                    mode='lines',
                    fill='tozeroy',
                    line=dict(color='green')
                ))
                fig2.update_layout(height=300, xaxis_title="交易次數", yaxis_title="資金")
                st.plotly_chart(fig2, use_container_width=True)
            
            # 交易記錄
            if results['trades']:
                st.subheader("📋 交易記錄")
                trades_df = pd.DataFrame(results['trades'])
                trades_df['time'] = trades_df['time'].astype(str)
                st.dataframe(trades_df, use_container_width=True)
        else:
            st.error("無法獲取數據，請檢查股票代碼")

# 說明
st.markdown("---")
st.markdown("""
### 📖 策略說明

| 策略 | 原理 | 適合情境 |
|------|------|----------|
| **突破策略** | 價格突破近期高點時買入 | 趨勢明顯時 |
| **反轉策略** | RSI超賣時買入，超買時賣出 | 區間震盪時 |
| **區間策略** | 接近支撐買入，接近壓力賣出 | 區間整理時 |
| **均線策略** | 短均線穿越長均線時交易 | 趨勢確認時 |
| **Gap and Go** | 跳空缺口後順勢交易 | 開盤跳空時 |
| **動能交易** | 強勢股順勢追蹤 | 趨勢延續時 |
| **VWAP 回歸** | 價格回歸 VWAP 均值 | 日內交易時 |
| **開盤區間突破** | 開盤後突破區間進場 | 開盤突破時 |

⚠️ **風險提示**：日內交易風險極高，過去績效不代表未來表現，請謹慎評估！
""")
