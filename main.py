import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 頁面配置 ---
st.set_page_config(page_title="Fitness Tracker Pro", layout="wide", page_icon="🏋️")

# --- 核心連線函數 ---
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_connection()

# --- 1. 讀取資料與自定義項目 ---
try:
    # 讀取主紀錄
    df = conn.read(worksheet="Records", ttl=0).dropna(how="all")
    
    # 讀取自定義運動項目清單 (從第二個分頁)
    exercise_df = conn.read(worksheet="Exercises", ttl=0).dropna(how="all")
    if not exercise_df.empty:
        exercise_list = exercise_df['項目名稱'].tolist()
    else:
        exercise_list = ["胸部訓練", "背部訓練", "腿部訓練"] # 初始預設值

    # 日期與數值格式修正 (處理 mixed format)
    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce').dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"連線或格式錯誤：{e}")
    st.stop()

# --- 標題 ---
st.title("🏋️ 高階健身與飲食管理系統")

# --- UI 佈局 ---
col_form, col_chart = st.columns([1, 1])

with col_form:
    st.subheader("📝 訓練與飲食登記")
    
    # 類別選擇
    log_type = st.radio("記錄類型", ["運動", "飲食"], horizontal=True)
    
    if log_type == "運動":
        # 子項目選擇與新增
        c1, c2 = st.columns([3, 1])
        with c1:
            sub_item = st.selectbox("訓練部位/項目", options=exercise_list)
        with c2:
            with st.popover("➕ 新增項目"):
                new_ex = st.text_input("新項目名稱")
                if st.button("永久儲存"):
                    if new_ex and new_ex not in exercise_list:
                        # 寫入 Exercises 分頁
                        new_ex_df = pd.DataFrame([{"項目名稱": new_ex}])
                        updated_ex_df = pd.concat([exercise_df, new_ex_df], ignore_index=True)
                        conn.update(worksheet="Exercises", data=updated_ex_df)
                        st.success("已儲存！")
                        st.rerun()

        # 重訓詳細資訊表單
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
            if st.form_submit_button("🚀 存入運動紀錄", use_container_width=True):
                full_item = f"{sub_item} ({weight}kg, {sets}x{reps})"
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
        # 飲食紀錄表單 (簡化版)
        with st.form("food_form", clear_on_submit=True):
            f_date = st.date_input("日期", datetime.now())
            food_item = st.text_input("食物/餐點名稱")
            food_kcal = st.number_input("攝取熱量(kcal)", min_value=0, value=500)
            if st.form_submit_button("🍎 存入飲食紀錄", use_container_width=True):
                new_data = pd.DataFrame([{
                    "日期": f_date.strftime("%Y-%m-%d"),
                    "類別": "飲食",
                    "項目": food_item,
                    "數值": food_kcal,
                    "備註": ""
                }])
                conn.update(worksheet="Records", data=pd.concat([df, new_data], ignore_index=True))
                st.success("寫入成功！")
                st.rerun()

with col_chart:
    st.subheader("📈 數據趨勢")
    if not df.empty:
        # 準備 Plotly 圖表數據
        chart_df = df.copy()
        # 依日期加總運動與飲食
        daily_stats = chart_df.groupby(['日期', '類別'])['數值'].sum().reset_index()
        
        fig = px.line(daily_stats, x='日期', y='數值', color='類別',
                      markers=True, title="每日熱量進出趨勢 (kcal)",
                      color_discrete_map={"運動": "#FF4B4B", "飲食": "#00CC96"})
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("**最近紀錄明細**")
        st.dataframe(df.tail(8), use_container_width=True, hide_index=True)
    else:
        st.info("尚無紀錄")

# --- 二次確認清除區 ---
st.divider()
st.subheader("⚙️ 管理區域")
c_del, c_reset = st.columns(2)

with c_del:
    with st.popover("🗑️ 刪除最後一筆紀錄", use_container_width=True):
        st.warning("確定刪除最後一筆紀錄？此動作不可逆。")
        if st.button("確認刪除", type="primary"):
            if not df.empty:
                conn.update(worksheet="Records", data=df.iloc[:-1])
                st.rerun()

with c_reset:
    if st.button("🧹 清除畫面暫存", use_container_width=True):
        st.rerun()
