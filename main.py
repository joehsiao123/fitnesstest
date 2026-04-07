import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import time

# --- 1. 頁面配置與高級感 CSS ---
st.set_page_config(page_title="Pro Fitness & Diet Lab", layout="wide", page_icon="⚖️")

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00cc96; }
    .stButton>button { border-radius: 8px; height: 3em; transition: 0.3s; }
    div.stButton > button:first-child { background-color: #4B9BFF; color: white; }
    .main-header { font-size: 2.2rem; font-weight: 800; margin-bottom: 1rem; color: #1E1E1E; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心連線與初始化 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def check_init():
    try:
        conn.read(worksheet="Records", ttl=0)
        conn.read(worksheet="Exercises", ttl=0)
    except:
        st.toast("正在初始化雲端資料庫結構...", icon="⚙️")
        # 建立初始結構
        conn.update(worksheet="Records", data=pd.DataFrame(columns=["日期", "類別", "項目", "數值", "備註"]))
        conn.update(worksheet="Exercises", data=pd.DataFrame([{"大項目":"胸","子項目":"臥推"}]))
        st.rerun()

check_init()

# --- 3. 資料讀取與清理 ---
try:
    df = conn.read(worksheet="Records", ttl=0).dropna(how="all")
    ex_master = conn.read(worksheet="Exercises", ttl=0).dropna(subset=['大項目', '子項目'])
    
    # 清理資料
    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce').dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
    
    # 建立運動字典 (去 nan)
    ex_master = ex_master[ex_master['子項目'].astype(str).str.lower() != 'nan']
    ex_dict = ex_master.groupby('大項目')['子項目'].apply(list).to_dict()
except Exception as e:
    st.error(f"連線異常: {e}")
    st.stop()

# --- 4. 側邊欄模式切換 (分開管理的核心) ---
with st.sidebar:
    st.title("🛡️ 管理中心")
    mode = st.radio("選擇管理模式", ["📊 數據總覽", "🏃 健身管理", "🥗 飲食管理"], index=0)
    st.divider()
    if st.button("🧹 刷新數據"): st.rerun()

# --- 5. 邏輯分流顯示 ---

# --- A. 數據總覽 (優化後的圖表) ---
if mode == "📊 數據總覽":
    st.markdown('<p class="main-header">數據趨勢分析</p>', unsafe_allow_html=True)
    
    if not df.empty:
        # 計算今日概況
        t_df = df[df['日期'] == datetime.now().date()]
        in_k = t_df[t_df['類別'] == '飲食']['數值'].sum()
        out_k = t_df[t_df['類別'] == '運動']['數值'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("今日攝取 (In)", f"{int(in_k)} kcal")
        m2.metric("今日消耗 (Out)", f"{int(out_k)} kcal")
        m3.metric("熱量淨值", f"{int(in_k - out_k)} kcal", delta=f"{int(in_k - out_k - 2000)} vs 基代", delta_color="inverse")

        # 優化圖表：使用雙軸或分開顯示
        st.subheader("🔥 熱量進出對比圖")
        daily_sum = df.groupby(['日期', '類別'])['數值'].sum().unstack(fill_value=0).reset_index()
        
        fig = go.Figure()
        if '飲食' in daily_sum.columns:
            fig.add_trace(go.Scatter(x=daily_sum['日期'], y=daily_sum['飲食'], name='攝取 (In)', fill='tozeroy', line_color='#00CC96'))
        if '運動' in daily_sum.columns:
            fig.add_trace(go.Bar(x=daily_sum['日期'], y=daily_sum['運動'], name='消耗 (Out)', marker_color='#FF4B4B', opacity=0.6))
        
        fig.update_layout(hovermode="x unified", template="simple_white", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("尚無數據，請切換至管理模式開始記錄。")

# --- B. 健身管理 ---
elif mode == "🏃 健身管理":
    st.markdown('<p class="main-header">健身紀錄與項目管理</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("workout_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            m_cat = st.selectbox("訓練部位", options=list(ex_dict.keys()))
            s_item = st.selectbox("動作項目", options=ex_dict.get(m_cat, ["請先新增"]))
            
            d1, d2, d3 = st.columns(3)
            with d1: sets = st.number_input("組數", 0, 20, 4)
            with d2: reps = st.number_input("次數", 0, 100, 12)
            with d3: weight = st.number_input("重量(kg)", 0, 500, 0)
            
            kcal = st.number_input("預估消耗", 0, 2000, 250)
            if st.form_submit_button("🔥 存入健身紀錄", use_container_width=True):
                with st.status("上傳中...") as s:
                    full_name = f"[{m_cat}] {s_item} | {weight}kg({sets}x{reps})"
                    new_row = pd.DataFrame([{"日期": f_date, "類別":"運動", "項目":full_name, "數值":kcal, "備註":""}])
                    conn.update(worksheet="Records", data=pd.concat([df, new_row], ignore_index=True))
                    s.update(label="儲存成功！", state="complete")
                    st.balloons()
                    time.sleep(1); st.rerun()
    with c2:
        st.write("### 🏋️ 訓練庫管理")
        with st.popover("➕ 新增動作/部位", use_container_width=True):
            new_m = st.text_input("大項 (如: 腿)")
            new_s = st.text_input("動作 (如: 深蹲)")
            if st.button("儲存項目"):
                new_ex = pd.DataFrame([{"大項目":new_m, "子項目":new_s}])
                conn.update(worksheet="Exercises", data=pd.concat([ex_master, new_ex], ignore_index=True))
                st.rerun()
        
        st.write("最近運動紀錄")
        st.dataframe(df[df['類別']=='運動'].tail(5), use_container_width=True, hide_index=True)

# --- C. 飲食管理 ---
elif mode == "🥗 飲食管理":
    st.markdown('<p class="main-header">飲食紀錄與熱量追蹤</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.form("diet_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            food = st.text_input("食物名稱", placeholder="雞肉沙拉")
            kcal = st.number_input("攝取熱量", 0, 5000, 600)
            if st.form_submit_button("🍎 存入飲食紀錄", use_container_width=True):
                with st.status("紀錄中...") as s:
                    new_row = pd.DataFrame([{"日期": f_date, "類別":"飲食", "項目":food, "數值":kcal, "備註":""}])
                    conn.update(worksheet="Records", data=pd.concat([df, new_row], ignore_index=True))
                    s.update(label="紀錄成功！", state="complete")
                    st.snow()
                    time.sleep(1); st.rerun()
    with c2:
        st.write("### 📊 本週攝取分布")
        diet_df = df[df['類別']=='飲食']
        if not diet_df.empty:
            fig_pie = px.pie(diet_df.tail(10), values='數值', names='項目', hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r)
            st.plotly_chart(fig_pie, use_container_width=True)
        st.dataframe(diet_df.tail(5), use_container_width=True, hide_index=True)
