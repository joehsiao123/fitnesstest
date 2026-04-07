import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import time

# --- 1. 頁面配置與 CSS 美化 ---
st.set_page_config(page_title="Fitness Pro Max", layout="wide", page_icon="🏋️")

st.markdown("""
<style>
    .stButton>button:active { transform: scale(0.95); transition: 0.1s; }
    div.stButton > button:first-child { background-color: #00cc96; color: white; border: none; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 1.2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心連線與自動初始化 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def initialize_sheets():
    """檢查並自動修復 Google Sheets 結構"""
    # 檢查 Records (主紀錄)
    try:
        conn.read(worksheet="Records", ttl=0)
    except Exception:
        st.toast("正在初始化 Records 分頁...", icon="🛠️")
        df_init = pd.DataFrame(columns=["日期", "類別", "項目", "數值", "備註"])
        conn.update(worksheet="Records", data=df_init)
        st.rerun()

    # 檢查 Exercises (運動庫)
    try:
        conn.read(worksheet="Exercises", ttl=0)
    except Exception:
        st.toast("正在初始化 Exercises 運動庫...", icon="📚")
        ex_init = pd.DataFrame([
            {"大項目": "胸", "子項目": "臥推"},
            {"大項目": "背", "子項目": "引體向上"},
            {"大項目": "腿", "子項目": "深蹲"},
            {"大項目": "肩膀", "子項目": "側平舉"}
        ])
        conn.update(worksheet="Exercises", data=ex_init)
        st.rerun()

initialize_sheets()

# --- 3. 讀取與清理數據 ---
try:
    df = conn.read(worksheet="Records", ttl=0).dropna(how="all")
    ex_master = conn.read(worksheet="Exercises", ttl=0).dropna(how="all")
    
    # 建立選單字典 {大項: [子項...]}
    if not ex_master.empty:
        exercise_dict = ex_master.groupby('大項目')['子項目'].apply(list).to_dict()
    else:
        exercise_dict = {"請新增大項": ["請新增子項"]}

    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce').dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"連線異常: {e}")
    st.stop()

# --- 4. 主介面佈局 ---
st.title("🏋️ 智慧健身管理系統")
col_form, col_chart = st.columns([1, 1], gap="large")

with col_form:
    tab_workout, tab_food = st.tabs(["🏃 運動紀錄", "🥗 飲食紀錄"])

    # --- 運動紀錄頁籤 ---
    with tab_workout:
        c1, c2 = st.columns(2)
        with c1:
            main_cat = st.selectbox("選擇訓練部位", options=list(exercise_dict.keys()), key="m_cat")
        with c2:
            sub_options = exercise_dict.get(main_cat, ["無項目"])
            sub_item = st.selectbox("選擇動作項目", options=sub_options, key="s_item")

        with st.popover("➕ 管理運動清單", use_container_width=True):
            st.write("### 為新部位新增項目")
            new_m = st.text_input("大項目名稱 (如: 手臂)")
            new_s_m = st.text_input("第一個動作名稱 (如: 彎舉)")
            if st.button("確認新增大項"):
                if new_m and new_s_m:
                    new_df = pd.DataFrame([{"大項目": new_m, "子項目": new_s_m}])
                    conn.update(worksheet="Exercises", data=pd.concat([ex_master, new_df], ignore_index=True))
                    st.success("新增成功！")
                    st.rerun()
            
            st.divider()
            st.write(f"### 為「{main_cat}」新增動作")
            new_s = st.text_input("新動作名稱")
            if st.button("確認新增動作"):
                if new_s:
                    new_df = pd.DataFrame([{"大項目": main_cat, "子項目": new_s}])
                    conn.update(worksheet="Exercises", data=pd.concat([ex_master, new_df], ignore_index=True))
                    st.success("新增成功！")
                    st.rerun()

        with st.form("workout_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            d1, d2, d3 = st.columns(3)
            with d1: sets = st.number_input("組數", min_value=0, value=4)
            with d2: reps = st.number_input("次數", min_value=0, value=12)
            with d3: weight = st.number_input("重量(kg)", min_value=0, value=0)
            
            f_kcal = st.number_input("預估消耗熱量(kcal)", min_value=0, value=250)
            note = st.text_input("訓練心得/備註")
            
            if st.form_submit_button("🚀 存入紀錄", use_container_width=True):
                with st.status("正在與雲端同步...", expanded=True) as s:
                    full_item = f"[{main_cat}] {sub_item} | {weight}kg ({sets}x{reps})"
                    new_row = pd.DataFrame([{
                        "日期": f_date.strftime("%Y-%m-%d"),
                        "類別": "運動", "項目": full_item, "數值": f_kcal, "備註": note
                    }])
                    conn.update(worksheet="Records", data=pd.concat([df, new_row], ignore_index=True))
                    s.update(label="✅ 紀錄成功！", state="complete", expanded=False)
                    st.toast(f"成功記錄: {sub_item}", icon="🏋️")
                    st.balloons()
                    time.sleep(1.2)
                    st.rerun()

    # --- 飲食紀錄頁籤 ---
    with tab_food:
        with st.form("food_form", clear_on_submit=True):
            f_date_f = st.date_input("日期", datetime.now(), key="food_date")
            food_item = st.text_input("餐點/食物名稱", placeholder="例如: 雞腿便當")
            food_kcal = st.number_input("攝取熱量(kcal)", min_value=0, value=600)
            food_note = st.text_input("飲食備註", placeholder="例如: 無糖")
            
            if st.form_submit_button("🍎 存入紀錄", use_container_width=True):
                with st.status("同步飲食數據...", expanded=True) as s_f:
                    new_row = pd.DataFrame([{
                        "日期": f_date_f.strftime("%Y-%m-%d"),
                        "類別": "飲食", "項目": food_item, "數值": food_kcal, "備註": food_note
                    }])
                    conn.update(worksheet="Records", data=pd.concat([df, new_row], ignore_index=True))
                    s_f.update(label="✅ 飲食紀錄成功！", state="complete", expanded=False)
                    st.toast(f"成功記錄: {food_item}", icon="🥗")
                    st.snow() # 飲食成功改噴雪花
                    time.sleep(1.2)
                    st.rerun()

with col_chart:
    st.subheader("📈 數據與趨勢分析")
    if not df.empty:
        # 計算今日熱量
        today_s = datetime.now().date()
        today_df = df[df['日期'] == today_s]
        in_k = today_df[today_df['類別'] == '飲食']['數值'].sum()
        out_k = today_df[today_df['類別'] == '運動']['數值'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("今日攝取 (In)", f"{int(in_k)} kcal")
        m2.metric("今日消耗 (Out)", f"{int(out_k)} kcal", delta=f"{int(in_k - out_k)} Net", delta_color="inverse")

        # 繪製圖表
        chart_df = df.groupby(['日期', '類別'])['數值'].sum().reset_index()
        fig = px.line(chart_df, x='日期', y='數值', color='類別', markers=True,
                      color_discrete_map={"運動": "#FF4B4B", "飲食": "#00CC96"},
                      template="plotly_white")
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("**最近紀錄明細**")
        st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("尚無紀錄，開始填寫第一筆資料吧！")

# --- 5. 管理區域 ---
st.divider()
with st.popover("🗑️ 刪除最後一筆紀錄 (危險區域)"):
    st.warning("確定要刪除最新的紀錄嗎？此動作不可撤銷。")
    if st.button("確認刪除最後一筆", type="primary", use_container_width=True):
        if not df.empty:
            conn.update(worksheet="Records", data=df.iloc[:-1])
            st.toast("已成功刪除紀錄", icon="🗑️")
            st.rerun()
