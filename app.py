import streamlit as st
import requests
import pandas as pd
import altair as alt

# =================== 設定區 ===================
# ⚠️ 請分別填入您 1H 和 4H 專案的 Firebase 網址 (記得結尾要有 / )
FIREBASE_URL_1H = "https://btc-ml-2-default-rtdb.firebaseio.com/" 
FIREBASE_URL_4H = "https://btc-ml-b62b7-default-rtdb.firebaseio.com/"
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

st.title("🤖 BTC AI 預測雷達")
st.write("雙時間級別：最新預測走勢與歷史紀錄")

if st.button("🔄 重新載入最新訊號"):
    st.rerun()

# 建立一個通用的渲染函數，這次改為接收完整的專案網址
def render_dashboard(project_url, title_prefix):
    try:
        # 後端腳本如果是上傳到預設的 latest_signals.json，這裡就直接接在網址後面
        # 確保網址組合正確（避免出現雙斜線 //）
        base_url = project_url.rstrip('/')
        full_url = f"{base_url}/latest_signals.json"
        
        response = requests.get(full_url)
        
        if response.status_code == 200 and response.json() is not None:
            data = response.json()
            
            # === 繪製彩色折線圖區塊 ===
            chart_data = []
            for item in data:
                sig = item.get("signal", "")
                if "SELL" in sig:
                    val = 1
                    color = "#e74c3c"
                    action = "🔴 賣出"
                elif "BUY" in sig:
                    val = -1
                    color = "#27ae60"
                    action = "🟢 買入"
                else:
                    val = 0
                    color = "#f1c40f"
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
            
            st.subheader(f"📈 {title_prefix} 近期決策趨勢")
            
            # 1. 畫出基礎的灰色折線
            line = alt.Chart(df).mark_line(color='gray', opacity=0.5).encode(
                x=alt.X('時間', sort=None, title='時間 (月-日 時:分)'),
                y=alt.Y('訊號位階', scale=alt.Scale(domain=[-1.5, 1.5]), title='', axis=alt.Axis(values=[-1, 0, 1]))
            )
            
            # 2. 在折線上疊加彩色的圓點
            points = alt.Chart(df).mark_circle(size=200, opacity=1).encode(
                x=alt.X('時間', sort=None),
                y=alt.Y('訊號位階'),
                color=alt.Color('顏色', scale=None),
                tooltip=['時間', '動作'] 
            )
            
            # 3. 結合線條與點點並顯示
            final_chart = (line + points).properties(height=250)
            st.altair_chart(final_chart, use_container_width=True)
            
            st.divider() 
            
            # === 歷史卡片區塊 ===
            st.subheader(f"📋 {title_prefix} 詳細紀錄")
            
            data.reverse() 
            
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
            st.info(f"目前 {title_prefix} 專案雲端還沒有資料。")
            
    except Exception as e:
        st.error(f"連線至 {title_prefix} 資料庫失敗：{e}")

# === 使用 Streamlit Tabs 建立分頁介面 ===
tab1, tab2 = st.tabs(["⚡ 1H 短線策略", "🛡️ 4H 波段策略"])

with tab1:
    # 傳入 1H 專案的網址
    render_dashboard(project_url=FIREBASE_URL_1H, title_prefix="1H")

with tab2:
    # 傳入 4H 專案的網址
    render_dashboard(project_url=FIREBASE_URL_4H, title_prefix="4H")
