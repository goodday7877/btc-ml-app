import streamlit as st
import requests
import pandas as pd
import altair as alt

# =================== 設定區 ===================
# ⚠️ 請將下方引號內的網址換成您的 Firebase Realtime Database 網址
FIREBASE_URL = "https://btc-ml-b62b7-default-rtdb.firebaseio.com/" 
# ==============================================

# 設定手機版網頁外觀
st.set_page_config(page_title="BTC AI 訊號雷達", page_icon="🤖", layout="centered")

st.markdown("""
<style>
    .signal-card {
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex;
        align-items: center; justify-content: space-between;
    }
    .buy-card { background-color: rgba(39, 174, 96, 0.1); border-left: 5px solid #27ae60; }
    .sell-card { background-color: rgba(231, 76, 60, 0.1); border-left: 5px solid #e74c3c; }
    .hold-card { background-color: rgba(241, 196, 15, 0.1); border-left: 5px solid #f1c40f; }
    .signal-icon { font-size: 20px; font-weight: bold; }
    .price-text { font-size: 16px; font-weight: bold; color: #333; }
    .time-text { font-size: 12px; color: #7f8c8d; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 BTC 4H AI 預測雷達")
st.write("最新預測走勢與歷史紀錄")

if st.button("🔄 重新載入最新訊號"):
    st.rerun()

try:
    response = requests.get(f"{FIREBASE_URL}/latest_signals.json")
    
    if response.status_code == 200 and response.json() is not None:
        data = response.json()
        
        # === 繪製彩色折線圖區塊 ===
        chart_data = []
        for item in data:
            sig = item.get("signal", "")
            # 數值設定：賣=1, 觀望=0, 買=-1
            if "SELL" in sig:
                val = 1
                color = "#e74c3c" # 紅色
                action = "🔴 賣出"
            elif "BUY" in sig:
                val = -1
                color = "#27ae60" # 綠色
                action = "🟢 買入"
            else:
                val = 0
                color = "#f1c40f" # 黃色
                action = "🟡 觀望"
                
            time_str = str(item.get("timestamp", ""))
            short_time = time_str[5:16] if len(time_str) >= 16 else time_str
            
            chart_data.append({
                "時間": short_time, 
                "訊號位階": val, 
                "動作": action,
                "顏色": color
            })
            
        df = pd.DataFrame(chart_data)
        
        st.subheader("📈 近期決策趨勢")
        
        # 1. 畫出基礎的灰色折線
        line = alt.Chart(df).mark_line(color='gray', opacity=0.5).encode(
            x=alt.X('時間', sort=None, title='時間 (月-日 時:分)'),
            y=alt.Y('訊號位階', scale=alt.Scale(domain=[-1.5, 1.5]), title='', axis=alt.Axis(values=[-1, 0, 1]))
        )
        
        # 2. 在折線上疊加彩色的圓點
        points = alt.Chart(df).mark_circle(size=200, opacity=1).encode(
            x=alt.X('時間', sort=None),
            y=alt.Y('訊號位階'),
            color=alt.Color('顏色', scale=None), # 使用我們自己定義的色碼
            tooltip=['時間', '動作'] # 滑鼠移過去會顯示詳細資訊
        )
        
        # 3. 結合線條與點點並顯示
        final_chart = (line + points).properties(height=250)
        st.altair_chart(final_chart, use_container_width=True)
        
        st.divider() # 分隔線
        
        # === 歷史卡片區塊 ===
        st.subheader("📋 詳細紀錄")
        
        data.reverse() # 最新的排在最上面
        
        for item in data:
            signal = item.get("signal", "⚪ HOLD")
            raw_price = item.get("price", 0)
            price = float(raw_price) if raw_price != "" else 0.0
            timestamp = item.get("timestamp", "")
            
            if "BUY" in signal:
                css_class = "buy-card"
                icon = "🟢 買入"
            elif "SELL" in signal:
                css_class = "sell-card"
                icon = "🔴 賣出"
            else:
                css_class = "hold-card"
                icon = "🟡 觀望"
            
            st.markdown(f"""
            <div class="signal-card {css_class}">
                <div>
                    <div class="signal-icon">{icon}</div>
                    <div class="time-text">{timestamp}</div>
                </div>
                <div class="price-text">${price:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("目前雲端還沒有資料。")
        
except Exception as e:
    st.error(f"無法連線至資料庫：{e}")
