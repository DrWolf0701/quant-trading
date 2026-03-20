"""
小熊美股投資部落格 - 主程式
導航頁面
"""

import streamlit as st

st.set_page_config(
    page_title="小熊美股投資",
    page_icon="🐻",
    layout="wide"
)

# 側邊欄導航
st.sidebar.title("🐻 小熊美股投資")
st.sidebar.markdown("---")

# 導航選單
page = st.sidebar.radio(
    "📊 導航",
    ["📈 量化交易", "⚡ 日內交易", "🤖 AI選股", "🎯 投資運勢"]
)

# 根據選擇載入不同頁面
if page == "📈 量化交易":
    st.switcher(
        body="載入中...",
        url="quant_trading"
    )
    import 量化交易系統
elif page == "⚡ 日內交易":
    import 日內交易系統
elif page == "🤖 AI選股":
    import ai_stock_picker
elif page == "🎯 投資運勢":
    import 投資運勢
