"""
美股量化交易系統 - Streamlit UI版
包含：
1. 數據獲取 (yfinance)
2. 技術指標計算
3. 雙均線策略回測
4. 圖表展示
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# 頁面設定
st.set_page_config(page_title="美股量化交易系統", layout="wide")

st.title("📈 美股量化交易系統")
st.markdown("---")

# 側邊欄 - 參數設定
with st.sidebar:
    st.header("⚙️ 參數設定")
    
    # 股票選擇
    stock_symbol = st.text_input("股票代碼", value="GOOGL")
    
    # 時間範圍
    date_range = st.selectbox(
        "時間範圍",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3
    )
    
    # 短均線
    short_ma = st.slider("短均線天數", 5, 50, 20)
    
    # 長均線
    long_ma = st.slider("長均線天數", 20, 200, 50)
    
    # 初始資金
    initial_capital = st.number_input("初始資金 ($)", value=10000)
    
    st.markdown("---")
    st.markdown("### 📊 策略說明")
    st.info("""
    **雙均線策略**：
    - 金叉（短均線突破長均線）→ 買入
    - 死叉（短均線跌破長均線）→ 賣出
    """)

# 獲取數據
@st.cache_data
def get_stock_data(symbol, period):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        return df
    except Exception as e:
        st.error(f"獲取數據失敗: {e}")
        return None

# 計算技術指標
def calculate_indicators(df, short_period, long_period):
    df = df.copy()
    
    # 計算均線
    df['SMA_short'] = df['Close'].rolling(window=short_period).mean()
    df['SMA_long'] = df['Close'].rolling(window=long_period).mean()
    
    # 計算 RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 計算 MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# 回測策略
def backtest(df, initial_capital):
    df = df.copy()
    
    # 初始化
    df['Signal'] = 0
    df.loc[df['SMA_short'] > df['SMA_long'], 'Signal'] = 1
    df['Position'] = df['Signal'].diff()
    
    # 模擬交易
    capital = initial_capital
    shares = 0
    trades = []
    portfolio_values = []  # 追蹤帳戶價值
    
    for i, row in df.iterrows():
        # 計算當前帳戶價值
        if shares > 0:
            current_value = shares * row['Close']
        else:
            current_value = capital
        portfolio_values.append({'date': i, 'value': current_value})
        
        if pd.isna(row['Position']) or row['Position'] == 0:
            continue
            
        if row['Position'] == 1:  # 買入訊號（金叉）
            shares = capital / row['Close']
            trades.append({
                'date': i,
                'type': 'BUY',
                'price': row['Close'],
                'shares': shares,
                'capital': capital
            })
            capital = 0
            
        elif row['Position'] == -1:  # 賣出訊號（死叉）
            if shares > 0:
                final_capital = shares * row['Close']
                trades.append({
                    'date': i,
                    'type': 'SELL',
                    'price': row['Close'],
                    'shares': shares,
                    'capital': final_capital
                })
                capital = final_capital
                shares = 0
    
    # 計算最終價值
    if shares > 0:
        final_value = shares * df.iloc[-1]['Close']
    else:
        final_value = capital
    
    # 計算勝率
    winning_trades = 0
    losing_trades = 0
    for i in range(1, len(trades), 2):
        if i < len(trades):
            sell_capital = trades[i]['capital']
            buy_capital = trades[i-1]['capital']
            if sell_capital > buy_capital:
                winning_trades += 1
            else:
                losing_trades += 1
    
    total_trades = winning_trades + losing_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    return final_value, trades, portfolio_values, win_rate, winning_trades, losing_trades

# 主程式
if stock_symbol:
    with st.spinner('載入數據中...'):
        df = get_stock_data(stock_symbol, date_range)
    
    if df is not None and len(df) > 0:
        # 計算指標
        df = calculate_indicators(df, short_ma, long_ma)
        
        # 計算交易（先用於買賣標記）
        final_value, trades, portfolio_values, win_rate, winning_trades, losing_trades = backtest(df, initial_capital)
        
        # 顯示基本資訊
        col1, col2, col3, col4 = st.columns(4)
        
        current_price = df.iloc[-1]['Close']
        price_change = df.iloc[-1]['Close'] - df.iloc[-2]['Close']
        price_change_pct = (price_change / df.iloc[-2]['Close']) * 100
        
        with col1:
            st.metric("目前股價", f"${current_price:.2f}")
        with col2:
            st.metric("漲跌", f"${price_change:.2f}", f"{price_change_pct:.2f}%")
        with col3:
            st.metric("RSI", f"{df.iloc[-1]['RSI']:.2f}")
        with col4:
            st.metric("MACD", f"{df.iloc[-1]['MACD']:.2f}")
        
        # 圖表 - K線圖 + 均線
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, 
                           subplot_titles=('股價 + 均線', '成交量'))
        
        # K線圖
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='股價'
        ), row=1, col=1)
        
        # 均線
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_short'], 
                                 mode='lines', name=f'SMA {short_ma}',
                                 line=dict(color='blue', width=1)), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_long'], 
                                 mode='lines', name=f'SMA {long_ma}',
                                 line=dict(color='red', width=1)), row=1, col=1)
        
        # 買賣標記
        for trade in trades:
            if trade['type'] == 'BUY':
                fig.add_trace(go.Scatter(
                    x=[trade['date']], 
                    y=[trade['price']],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=15, color='green'),
                    name='買入'
                ), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(
                    x=[trade['date']], 
                    y=[trade['price']],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    name='賣出'
                ), row=1, col=1)
        
        # 成交量
        colors = ['green' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else 'red' 
                  for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], 
                             name='成交量', marker_color=colors), row=2, col=1)
        
        fig.update_layout(
            height=600,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # RSI 圖
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], 
                                     mode='lines', name='RSI',
                                     line=dict(color='purple', width=2)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", 
                         annotation_text="超買")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", 
                         annotation_text="超賣")
        fig_rsi.update_layout(height=200, title="RSI 指標")
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # 回測結果
        st.markdown("---")
        st.subheader("🔄 回測結果")
        
        returns = (final_value - initial_capital) / initial_capital * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("初始資金", f"${initial_capital:,.2f}")
        with col2:
            st.metric("最終價值", f"${final_value:,.2f}")
        with col3:
            st.metric("報酬率", f"{returns:.2f}%", 
                      delta=f"{returns:.2f}%")
        with col4:
            st.metric("勝率", f"{win_rate:.1f}%")
        
        # 帳戶價值趨勢圖
        if portfolio_values:
            st.markdown("### 📈 帳戶盈虧趨勢")
            portfolio_df = pd.DataFrame(portfolio_values)
            
            fig_portfolio = go.Figure()
            fig_portfolio.add_trace(go.Scatter(
                x=portfolio_df['date'], 
                y=portfolio_df['value'],
                mode='lines',
                name='帳戶價值',
                line=dict(color='green', width=2)
            ))
            fig_portfolio.add_hline(y=initial_capital, line_dash="dash", 
                                   line_color="gray", annotation_text="初始資金")
            fig_portfolio.update_layout(
                height=300,
                xaxis_title="日期",
                yaxis_title="帳戶價值 ($)"
            )
            st.plotly_chart(fig_portfolio, use_container_width=True)
        
        # 交易記錄
        if trades:
            st.markdown("### 📝 交易記錄")
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ 獲利交易: {winning_trades} 次")
            with col2:
                st.error(f"❌ 虧損交易: {losing_trades} 次")
            
            trades_df = pd.DataFrame(trades)
            trades_df['date'] = trades_df['date'].dt.strftime('%Y-%m-%d')
            st.dataframe(trades_df, use_container_width=True)
        else:
            st.warning("沒有產生交易訊號")
            
    else:
        st.error("無法獲取數據，請檢查股票代碼是否正確")
