"""
小熊美股投資 - 導航頁面
"""

import streamlit as st

st.set_page_config(
    page_title="小熊美股投資",
    page_icon="🐻",
    layout="wide"
)

st.title("🐻 小熊美股投資")
st.markdown("---")

# 側邊欄導航
st.sidebar.title("📊 導航選單")

page = st.sidebar.selectbox(
    "選擇功能",
    ["🤖 AI選股", "📈 量化交易", "⚡ 日內交易", "🎯 投資運勢"]
)

# 根據選擇載入不同頁面
if page == "🤖 AI選股":
    exec(open("ai_stock_picker.py").read())
elif page == "📈 量化交易":
    exec(open("量化交易系統.py").read())
elif page == "⚡ 日內交易":
    exec(open("日內交易系統.py").read())
elif page == "🎯 投資運勢":
    exec(open("投資運勢.py").read())
