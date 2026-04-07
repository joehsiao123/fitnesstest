import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 頁面配置 ---
st.set_page_config(page_title="Fitness Self-Healing App", layout="wide", page_icon="🛡️")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 🛠️ 自動初始化函數 ---
def initialize_sheets():
    """檢查並初始化 Google Sheets 的分頁與標題"""
    # 1. 檢查/初始化主紀錄表 (Records)
    try:
        df_check = conn.read(worksheet="Records", ttl=0)
    except Exception:
        st.warning("檢測到缺少 Records 分頁，正在自動建立...")
        initial_records = pd.DataFrame(columns=["日期", "類別", "項目", "數值", "備註"])
        conn.update(worksheet="Records", data=initial_records)
        st.rerun()

    # 2. 檢查/初始化運動庫 (Exercises)
    try:
        ex_check = conn.read(worksheet="Exercises", ttl=0)
    except Exception:
        st.warning("檢測到缺少 Exercises 分頁，正在自動建立預設選單...")
        initial_exercises = pd.DataFrame([
            {"大項目": "胸", "子項目": "臥推"},
            {"大項目": "背", "子項目": "引體向上"},
            {"大項目": "腿", "子項目": "深蹲"},
            {"大項目": "肩膀", "子項目": "側平舉"}
        ])
        conn.update(worksheet="Exercises", data=initial_exercises)
        st.rerun()

# 執行初始化檢查
initialize_sheets()

# --- 1. 讀取資料與層級選單 ---
try:
    df = conn.read(worksheet="Records", ttl=0).dropna(how="all")
    ex_master = conn.read(worksheet="Exercises", ttl=0).dropna(how="all")
    
    # 建立選單字典
    if not ex_master.empty:
        exercise_dict = ex_master.groupby('大項目')['子項目'].apply(list).to_dict()
    else:
        exercise_dict = {"請新增大項": ["請新增子項"]}

    # 格式清理
    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce').dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"資料讀取失敗，請確認 Service Account 權限：{e}")
    st.stop()

# --- 標題 ---
st.title("🛡️ 智慧型健身管理系統 (自動修復版)")

# --- UI 佈局 ---
col_form, col_chart = st.columns([1, 1])

with col_form:
    st.subheader("📝 快速紀錄")
    log_type = st.radio("記錄類型", ["運動", "飲食"], horizontal=True)
    
    if log_type == "運動":
        c1, c2 = st.columns(2)
        with c1:
            main_cat = st.selectbox("1. 選擇大項目 (部位)", options=list(exercise_dict.keys()))
        with c2:
            sub_options = exercise_dict.get(main_cat, ["請先新增子項目"])
            sub_item = st.selectbox("2. 選擇子項目 (動作)", options=sub_options)

        # --- 層級化新增功能 ---
        with st.popover("➕ 管理運動清單"):
            st.write("### 新增大項目")
            new_main = st.text_input("輸入新部位名稱 (如：手臂)")
            new_sub_for_main = st.text_input("輸入該部位的第一個動作 (如：二頭彎舉)")
            if st.button("新增大項與動作"):
                if new_main and new_sub_for_main:
                    new_ex_df = pd.DataFrame([{"大項目": new_main, "子項目": new_sub_for_main}])
                    updated_ex = pd.concat([ex_master, new_ex_df], ignore_index=True)
                    conn.update(worksheet="Exercises", data=updated_ex)
                    st.rerun()
            
            st.divider()
            st.write(f"### 為「{main_cat}」新增動作")
            new_sub = st.text_input("輸入新動作名稱")
            if st.button("僅新增子動作"):
                if new_sub:
                    new_ex_df = pd.DataFrame([{"大項目": main_cat, "子項目": new_sub}])
                    updated_ex = pd.concat([ex_master, new_ex_df], ignore_index=True)
                    conn.update(worksheet="Exercises", data=updated_ex)
                    st.rerun()

        # --- 詳細紀錄表單 ---
        with st.form("workout_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            d1, d2, d3 = st.columns(3)
            with d1: sets = st.number_input("組數", min_value=0, value=4)
            with d2: reps = st.number_input("次數", min_value=0, value=12)
            with d3: weight = st.number_input("重量(kg)", min_value=0, value=0)
            
            f_kcal = st.number_input("消耗熱量(kcal)", min_value=0, value=250)
            note = st.text_input("備註")
            
            if st.form_submit_button("🚀 存入紀錄", use_container_width=True):
                full_item = f"[{main_cat}] {sub_item} | {weight}kg ({sets}x{reps})"
                new_data = pd.DataFrame([{
                    "日期": f_date.strftime("%Y-%m-%d"),
                    "類別": "運動", "項目": full_item, "數值": f_kcal, "備註": note
                }])
                conn.update(worksheet="Records", data=pd.concat([df, new_data], ignore_index=True))
                st.success("寫入成功！")
                st.rerun()

    else:
        # 飲食紀錄
        with st.form("food_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            food_item = st.text_input("餐點名稱")
            food_kcal = st.number_input("攝取熱量(kcal)", min_value=0, value=500)
            if st.form_submit_button("🍎 存入紀錄", use_container_width=True):
                new_data = pd.DataFrame([{
                    "日期": f_date.strftime("%Y-%m-%d"),
                    "類別": "飲食", "項目": food_item, "數值": food_kcal, "備註": ""
                }])
                conn.update(worksheet="Records", data=pd.concat([df, new_data], ignore_index=True))
                st.rerun()

with col_chart:
    st.subheader("📈 趨勢分析")
    if not df.empty:
        daily_stats = df.groupby(['日期', '類別'])['數值'].sum().reset_index()
        fig = px.line(daily_stats, x='日期', y='數值', color='類別', markers=True,
                      color_discrete_map={"運動": "#FF4B4B", "飲食": "#00CC96"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("尚無紀錄，請先填寫左側表單。")

# --- 二次確認清除區 ---
st.divider()
with st.popover("🗑️ 刪除最後一筆紀錄"):
    st.warning("確定刪除最後一筆資料？")
    if st.button("確認刪除", type="primary"):
        if not df.empty:
            conn.update(worksheet="Records", data=df.iloc[:-1])
            st.rerun()
