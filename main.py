import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import time

# --- 1. 頁面配置與 CSS 強化 ---
st.set_page_config(page_title="Fitness Tracker Pro", layout="wide", page_icon="🏋️")

st.markdown("""
<style>
    /* 按鈕點擊位移感 */
    .stButton>button:active { transform: scale(0.98); transition: 0.1s; }
    /* 儲存按鈕顏色 */
    div.stButton > button:first-child { background-color: #00cc96; color: white; border: none; }
    /* 頁籤文字放大 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 1.1rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心連線與自我修復初始化 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def initialize_sheets():
    """自動偵測並建立缺失的分頁與標題列"""
    try:
        conn.read(worksheet="Records", ttl=0)
    except Exception:
        st.toast("正在初始化主紀錄表...", icon="🛠️")
        df_init = pd.DataFrame(columns=["日期", "類別", "項目", "數值", "備註"])
        conn.update(worksheet="Records", data=df_init)
        st.rerun()

    try:
        conn.read(worksheet="Exercises", ttl=0)
    except Exception:
        st.toast("正在初始化運動庫...", icon="📚")
        ex_init = pd.DataFrame([
            {"大項目": "胸", "子項目": "臥推"},
            {"大項目": "腿", "子項目": "深蹲"}
        ])
        conn.update(worksheet="Exercises", data=ex_init)
        st.rerun()

initialize_sheets()

# --- 3. 資料讀取與「去 nan」清理邏輯 ---
try:
    # 讀取主紀錄
    df = conn.read(worksheet="Records", ttl=0).dropna(how="all")
    
    # 讀取運動庫並強制過濾空值與 nan 字串
    ex_master = conn.read(worksheet="Exercises", ttl=0).dropna(subset=['大項目', '子項目'])
    ex_master['大項目'] = ex_master['大項目'].astype(str).str.strip()
    ex_master['子項目'] = ex_master['子項目'].astype(str).str.strip()
    # 過濾掉任何形式的空字串或 nan 字眼
    ex_master = ex_master[ex_master['子項目'].str.lower() != 'nan']
    ex_master = ex_master[ex_master['子項目'] != '']
    
    # 建立選單字典
    if not ex_master.empty:
        exercise_dict = ex_master.groupby('大項目')['子項目'].apply(list).to_dict()
    else:
        exercise_dict = {"請新增大項": ["請新增子項"]}

    # 格式化主紀錄資料
    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce').dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"資料加載失敗: {e}")
    st.stop()

# --- 4. 主介面：左側表單 ---
st.title("🏋️ 專業健身管理系統")
col_form, col_chart = st.columns([1, 1], gap="large")

with col_form:
    tab_workout, tab_food = st.tabs(["🏃 運動訓練", "🥗 飲食紀錄"])

    # --- 運動紀錄 ---
    with tab_workout:
        c1, c2 = st.columns(2)
        with c1:
            main_cat = st.selectbox("1. 訓練部位", options=list(exercise_dict.keys()), key="m_cat")
        with c2:
            # 確保子選單不會出現 nan
            sub_options = [s for s in exercise_dict.get(main_cat, []) if str(s).lower() != 'nan' and s]
            if not sub_options: sub_options = ["請先點選下方管理新增動作"]
            sub_item = st.selectbox("2. 動作項目", options=sub_options, key="s_item")

        # 管理功能 (Popover)
        with st.popover("⚙️ 管理項目庫 (新增後自動關閉)", use_container_width=True):
            st.write("### 新增大項目與動作")
            new_m = st.text_input("大項 (如: 手臂)")
            new_s_m = st.text_input("子項 (如: 彎舉)")
            if st.button("確認新增大項", use_container_width=True):
                if new_m and new_s_m:
                    new_df = pd.DataFrame([{"大項目": new_m, "子項目": new_s_m}])
                    conn.update(worksheet="Exercises", data=pd.concat([ex_master, new_df], ignore_index=True))
                    st.toast(f"✅ 已新增部位: {new_m}")
                    time.sleep(0.5)
                    st.rerun() # 藉由重整關閉彈窗
            
            st.divider()
            st.write(f"### 為「{main_cat}」新增動作")
            new_s = st.text_input("新動作名稱 (如: 哈克深蹲)")
            if st.button("確認新增動作", use_container_width=True):
                if new_s:
                    new_df = pd.DataFrame([{"大項目": main_cat, "子項目": new_s}])
                    conn.update(worksheet="Exercises", data=pd.concat([ex_master, new_df], ignore_index=True))
                    st.toast(f"✅ 已新增動作: {new_s}")
                    time.sleep(0.5)
                    st.rerun() # 藉由重整關閉彈窗

        # 核心輸入表單
        with st.form("workout_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            d1, d2, d3 = st.columns(3)
            with d1: sets = st.number_input("組數", min_value=0, value=4)
            with d2: reps = st.number_input("次數", min_value=0, value=12)
            with d3: weight = st.number_input("重量(kg)", min_value=0, value=0)
            f_kcal = st.number_input("消耗熱量(kcal)", min_value=0, value=250)
            note = st.text_input("備註 (例如：RPE 8)")
            
            if st.form_submit_button("🚀 存入運動紀錄", use_container_width=True):
                with st.status("同步雲端資料...", expanded=True) as s:
                    full_item = f"[{main_cat}] {sub_item} | {weight}kg ({sets}x{reps})"
                    new_row = pd.DataFrame([{
                        "日期": f_date.strftime("%Y-%m-%d"),
                        "類別": "運動", "項目": full_item, "數值": f_kcal, "備註": note
                    }])
                    conn.update(worksheet="Records", data=pd.concat([df, new_row], ignore_index=True))
                    s.update(label="✅ 成功儲存！", state="complete", expanded=False)
                    st.balloons()
                    time.sleep(1.2)
                    st.rerun()

    # --- 飲食紀錄 ---
    with tab_food:
        with st.form("food_form", clear_on_submit=True):
            f_date_f = st.date_input("日期", datetime.now(), key="f_date")
            food_item = st.text_input("食物名稱", placeholder="雞肉沙拉")
            food_kcal = st.number_input("攝取熱量(kcal)", min_value=0, value=500)
            if st.form_submit_button("🍱 存入飲食紀錄", use_container_width=True):
                with st.status("同步飲食資料...", expanded=True) as sf:
                    new_row = pd.DataFrame([{
                        "日期": f_date_f.strftime("%Y-%m-%d"),
                        "類別": "飲食", "項目": food_item, "數值": food_kcal, "備註": ""
                    }])
                    conn.update(worksheet="Records", data=pd.concat([df, new_row], ignore_index=True))
                    sf.update(label="✅ 飲食已紀錄！", state="complete", expanded=False)
                    st.snow()
                    time.sleep(1.2)
                    st.rerun()

# --- 5. 主介面：右側數據統計 ---
with col_chart:
    st.subheader("📊 今日數據概覽")
    if not df.empty:
        today_s = datetime.now().date()
        today_df = df[df['日期'] == today_s]
        in_k = today_df[today_df['類別'] == '飲食']['數值'].sum()
        out_k = today_df[today_df['類別'] == '運動']['數值'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("今日攝取 (In)", f"{int(in_k)} kcal")
        m2.metric("今日消耗 (Out)", f"{int(out_k)} kcal", delta=f"{int(in_k - out_k)} Net")

        # 趨勢圖表
        chart_df = df.groupby(['日期', '類別'])['數值'].sum().reset_index()
        fig = px.line(chart_df, x='日期', y='數值', color='類別', markers=True,
                      color_discrete_map={"運動": "#FF4B4B", "飲食": "#00CC96"},
                      template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("**最近 5 筆紀錄明細**")
        st.dataframe(df.tail(5), use_container_width=True, hide_index=True)
    else:
        st.info("尚無數據，請開始記錄。")

# --- 6. 管理與危險區域 ---
st.divider()
with st.popover("🗑️ 刪除最後一筆紀錄"):
    st.warning("刪除後無法復原，請確認。")
    if st.button("確認刪除", type="primary", use_container_width=True):
        if not df.empty:
            conn.update(worksheet="Records", data=df.iloc[:-1])
            st.toast("已刪除最後一筆紀錄")
            st.rerun()
