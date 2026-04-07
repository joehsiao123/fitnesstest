import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 頁面配置 ---
st.set_page_config(page_title="Fitness Pro Tiered", layout="wide", page_icon="🏋️")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. 讀取資料與層級選單 ---
try:
    # 讀取主紀錄
    df = conn.read(worksheet="Records", ttl=0).dropna(how="all")
    
    # 讀取運動庫 (大項與子項)
    ex_master = conn.read(worksheet="Exercises", ttl=0).dropna(how="all")
    
    # 將資料轉換成層級字典 {大項: [子項1, 子項2]}
    if not ex_master.empty:
        exercise_dict = ex_master.groupby('大項目')['子項目'].apply(list).to_dict()
    else:
        # 初始預設資料庫
        exercise_dict = {
            "胸": ["臥推", "啞鈴飛鳥"],
            "背": ["引體向上", "滑輪下拉"],
            "腿": ["哈克深蹲", "保加利亞分腿蹲"],
            "肩膀": ["側平舉", "軍事推舉"]
        }

    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce').dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"連線或資料表結構錯誤：{e}")
    st.stop()

# --- 標題 ---
st.title("🏋️ 專業層級健身管理系統")

# --- UI 佈局 ---
col_form, col_chart = st.columns([1, 1])

with col_form:
    st.subheader("📝 訓練登記")
    
    log_type = st.radio("記錄類型", ["運動", "飲食"], horizontal=True)
    
    if log_type == "運動":
        # --- 連動選單邏輯 ---
        c1, c2 = st.columns(2)
        with c1:
            main_cat = st.selectbox("1. 選擇大項目 (部位)", options=list(exercise_dict.keys()))
        with c2:
            sub_options = exercise_dict.get(main_cat, [])
            sub_item = st.selectbox("2. 選擇子項目 (動作)", options=sub_options)

        # --- 新增自定義子項目 ---
        with st.popover("➕ 新增訓練動作"):
            st.write(f"目前正在為「{main_cat}」新增動作")
            new_sub = st.text_input("輸入新動作名稱 (如：槓鈴深蹲)")
            if st.button("永久儲存至雲端"):
                if new_sub and new_sub not in sub_options:
                    new_ex_df = pd.DataFrame([{"大項目": main_cat, "子項目": new_sub}])
                    updated_ex_master = pd.concat([ex_master, new_ex_df], ignore_index=True)
                    conn.update(worksheet="Exercises", data=updated_ex_master)
                    st.success(f"已將 {new_sub} 加入 {main_cat}！")
                    st.rerun()

        # --- 詳細紀錄表單 ---
        with st.form("workout_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            d1, d2, d3 = st.columns(3)
            with d1: sets = st.number_input("組數", min_value=0, value=4)
            with d2: reps = st.number_input("次數", min_value=0, value=12)
            with d3: weight = st.number_input("重量(kg)", min_value=0, value=0)
            
            t1, t2 = st.columns(2)
            with t1: duration = st.number_input("耗時(分)", min_value=0, value=60)
            with t2: kcal = st.number_input("消耗熱量(kcal)", min_value=0, value=250)
            
            note = st.text_input("訓練備註")
            if st.form_submit_button("🚀 存入紀錄", use_container_width=True):
                full_item = f"[{main_cat}] {sub_item} | {weight}kg ({sets}x{reps})"
                new_data = pd.DataFrame([{
                    "日期": f_date.strftime("%Y-%m-%d"),
                    "類別": "運動",
                    "項目": full_item,
                    "數值": kcal,
                    "備註": f"{duration}分 | {note}"
                }])
                conn.update(worksheet="Records", data=pd.concat([df, new_data], ignore_index=True))
                st.success("寫入成功！")
                st.rerun()

    else:
        # 飲食紀錄 (保持簡約)
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
    st.subheader("📈 數據趨勢")
    if not df.empty:
        daily_stats = df.groupby(['日期', '類別'])['數值'].sum().reset_index()
        fig = px.line(daily_stats, x='日期', y='數值', color='類別', markers=True,
                      color_discrete_map={"運動": "#FF4B4B", "飲食": "#00CC96"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("尚無紀錄")

# --- 二次確認清除區 ---
st.divider()
with st.popover("🗑️ 刪除最後一筆紀錄"):
    st.warning("確定刪除？此動作不可逆。")
    if st.button("確認刪除", type="primary"):
        if not df.empty:
            conn.update(worksheet="Records", data=df.iloc[:-1])
            st.rerun()
