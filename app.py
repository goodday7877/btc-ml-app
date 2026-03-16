import streamlit as st
import requests
import pandas as pd
import altair as alt

# =================== 設定區 ===================
# ⚠️ 請分別填入您 1H 和 4H 專案的 Firebase 網址 (記得結尾要有 / )
FIREBASE_URL_1H = "https://btc-ml-2-default-rtdb.firebaseio.com/" 
FIREBASE_URL_4H = "https://btc-ml-b62b7-default-rtdb.firebaseio.com/"

# 要交易/顯示的幣種列表 (需與後端設定一致)
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
# ==============================================

# 設定手機版網頁外觀
st.set_page_config(page_title="AI 預測雷達", page_icon="🤖", layout="centered")

st.markdown("""
<style>
    .signal-card {
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex;
        align-items: center; justify-content: space-between;
    }
    .buy-card { background-color: rgba(39, 174, 96, 0.1); border-left: 5px solid #27ae60; }
    .sell-card { background-color: rgba(231, 76, 60, 0.1); border-left: 5px solid #e74c3c; }
    .hold-card { background-color: rgba(236, 240, 241, 0.5); border-left: 5px solid #bdc3c7; }
    .signal-icon { font-size: 18px; font-weight: bold; display: flex; align-items: center; gap: 8px; }
    .symbol-text { font-size: 16px; color: #444; background: #fff; padding: 2px 6px; border-radius: 4px; border: 1px solid #ddd; }
    .price-text { font-size: 16px; font-weight: bold; color: #333; }
    .time-text { font-size: 12px; color: #7f8c8d; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 多幣種 AI 預測雷達")
st.write("雙時間級別：所有幣種趨勢一目了然")

if st.button("🔄 重新載入最新訊號"):
    st.rerun()

def render_combined_dashboard(project_url, title_prefix):
    all_data = []
    
    # 1. 抓取所有幣種的資料
    for symbol in SYMBOLS:
        sym_firebase_key = symbol.replace('/', '_')
        base_url = project_url.rstrip('/')
        full_url = f"{base_url}/live_signals/{sym_firebase_key}.json"
        
        try:
            response = requests.get(full_url)
            if response.status_code == 200 and response.json() is not None:
                data_dict = response.json()
                data_list = list(data_dict.values())
                
                # 【修改】依時間排序並取最近的 10 筆，避免圖表過載
                data_list.sort(key=lambda x: x.get('timestamp', ''))
                for item in data_list[-10:]:
                    item['symbol'] = symbol
                    all_data.append(item)
        except Exception as e:
            st.error(f"連線至 {symbol} 資料庫失敗：{e}")

    if not all_data:
        st.info(f"目前 {title_prefix} 專案雲端還沒有任何資料。")
        return

    # 2. 準備繪圖資料
    chart_data = []
    offsets = {'BTC/USDT': 1.5, 'ETH/USDT': 0.0, 'BNB/USDT': -1.5}
    
    for item in all_data:
        sig = item.get("signal", "")
        sym = item.get("symbol", "")
        
        if "SELL" in sig:
            base_val = 1
            action = "🔴 賣出"
        elif "BUY" in sig:
            base_val = -1
            action = "🟢 買入"
        else:
            base_val = 0
            action = "⚪ 觀望" # 配合現貨模型更新為觀望
            
        val = base_val + offsets.get(sym, 0)
        time_str = str(item.get("timestamp", ""))
        short_time = time_str[5:16] if len(time_str) >= 16 else time_str
        price = float(item.get("price", 0)) if item.get("price", "") != "" else 0.0
        
        chart_data.append({
            "時間": short_time, 
            "訊號位階": val, 
            "動作": action,
            "幣種": sym,
            "價格": price
        })
        
    df = pd.DataFrame(chart_data)
    
    st.subheader(f"📈 {title_prefix} 多幣種綜合趨勢")
    
    # 繪製各幣種專屬的趨勢線
    line = alt.Chart(df).mark_line(opacity=0.7, strokeWidth=3).encode(
        x=alt.X('時間', sort=None, title='時間 (月-日 時:分)'),
        y=alt.Y('訊號位階', scale=alt.Scale(domain=[-3.0, 3.0]), axis=alt.Axis(labels=False, ticks=False, title='位階 (上帶:BTC / 中帶:ETH / 下帶:BNB)')),
        color=alt.Color('幣種', scale=alt.Scale(
            domain=['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
            range=['#3498db', '#9b59b6', '#e67e22'] 
        ), title="幣種連線"),
        detail='幣種' 
    )
    
    # 繪製圖示點
    points = alt.Chart(df).mark_point(size=180, opacity=1, filled=True).encode(
        x=alt.X('時間', sort=None),
        y=alt.Y('訊號位階'),
        color=alt.Color('動作', scale=alt.Scale(
            domain=['🟢 買入', '🔴 賣出', '⚪ 觀望'],
            range=['#27ae60', '#e74c3c', '#bdc3c7']
        ), title="動作"),
        shape=alt.Shape('幣種', scale=alt.Scale(
            domain=['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
            range=['circle', 'square', 'triangle'] 
        ), title="幣種圖示"),
        tooltip=['時間', '幣種', '動作', '價格']
    )
    
    # 合併顯示
    final_chart = (line + points).properties(height=380)
    st.altair_chart(final_chart, use_container_width=True)
    
    st.divider() 
    
    # 3. 綜合歷史卡片區塊
    st.subheader(f"📋 {title_prefix} 最新 10 筆動態列")
    
    # 混合排序：最新到最舊
    all_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # 【修改】只抓取總資料列的前 10 筆
    for item in all_data[:10]:
        signal = item.get("signal", "⚪ WAIT")
        raw_price = item.get("price", 0)
        price = float(raw_price) if raw_price != "" else 0.0
        timestamp = item.get("timestamp", "")
        sym = item.get("symbol", "")
        
        if "BUY" in signal:
            css_class = "buy-card"
            icon = "🟢"
        elif "SELL" in signal:
            css_class = "sell-card"
            icon = "🔴"
        else:
            css_class = "hold-card"
            icon = "⚪"
        
        st.markdown(f"""
        <div class="signal-card {css_class}">
            <div>
                <div class="signal-icon">{icon} <span class="symbol-text">{sym}</span></div>
                <div class="time-text">{timestamp}</div>
            </div>
            <div class="price-text">${price:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

# === 使用 Streamlit Tabs 建立主分頁 ===
tab1, tab2 = st.tabs(["⚡ 1H 短線策略", "🛡️ 4H 波段策略"])

with tab1:
    render_combined_dashboard(project_url=FIREBASE_URL_1H, title_prefix="1H")

with tab2:
    render_combined_dashboard(project_url=FIREBASE_URL_4H, title_prefix="4H")
