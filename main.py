import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px # 用於更精美的圖表

# --- 頁面配置 ---
st.set_page_config(page_title="Fitness Pro Max", layout="wide", page_icon="🏋️")

# --- 核心連線 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0).dropna(how="all")
    # 確保數值與日期格式正確
    if not df.empty:
        df['日期'] = pd.to_datetime(df['日期']).dt.date
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce')
except Exception as e:
    st.error(f"連線失敗：{e}")
    st.stop()

# --- 1. 自定義子項目管理 (利用 Session State 常駐) ---
if "custom_exercises" not in st.session_state:
    # 預設基礎項目
    st.session_state.custom_exercises = ["胸部訓練", "背部訓練", "腿部訓練", "肩部訓練", "核心訓練"]

# --- 標題 ---
st.title("🏋️ 高階健身訓練紀錄系統")

# --- UI 佈局 ---
col_form, col_chart = st.columns([1, 1])

with col_form:
    st.subheader("📝 訓練登記")
    
    # 類別選擇
    log_type = st.selectbox("運動大類", ["重訓", "有氧", "伸展"])
    
    # 子項目選擇與新增
    c1, c2 = st.columns([3, 1])
    with c1:
        sub_item = st.selectbox("選擇訓練部位/項目", options=st.session_state.custom_exercises)
    with c2:
        # 彈出視窗新增自定義項目
        with st.popover("➕ 新增"):
            new_exercise = st.text_input("輸入新項目名稱")
            if st.button("確認新增"):
                if new_exercise and new_exercise not in st.session_state.custom_exercises:
                    st.session_state.custom_exercises.append(new_exercise)
                    st.rerun()

    # 詳細資訊表單
    with st.form("detail_form", clear_on_submit=True):
        f_date = st.date_input("訓練日期", datetime.now())
        
        d_col1, d_col2, d_col3 = st.columns(3)
        with d_col1:
            sets = st.number_input("組數 (Sets)", min_value=0, value=4)
        with d_col2:
            reps = st.number_input("次數 (Reps)", min_value=0, value=12)
        with d_col3:
            weight = st.number_input("重量 (kg)", min_value=0, value=0)
            
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            f_time = st.number_input("耗時 (分鐘)", min_value=0, value=60)
        with t_col2:
            f_kcal = st.number_input("預估消耗熱量 (kcal)", min_value=0, value=250)
            
        f_note = st.text_input("備註", placeholder="例如：今天挑戰 PR 成功")
        
        if st.form_submit_button("🚀 存入雲端紀錄", use_container_width=True):
            try:
                # 整合項目名稱
                full_item = f"{log_type}-{sub_item} ({weight}kg, {sets}x{reps})"
                new_row = pd.DataFrame([{
                    "日期": f_date,
                    "類別": "運動",
                    "項目": full_item,
                    "數值": f_kcal,
                    "備註": f_note
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"已記錄：{full_item}")
                st.rerun()
            except Exception as ex:
                st.error(f"寫入失敗：{ex}")

with col_chart:
    st.subheader("📈 訓練趨勢分析")
    if not df.empty:
        # 準備圖表數據：按日期加總消耗熱量
        chart_data = df[df['類別'] == '運動'].groupby('日期')['數值'].sum().reset_index()
        
        if not chart_data.empty:
            # 使用 Plotly 畫出更漂亮的折線圖
            fig = px.line(chart_data, x='日期', y='數值', title='每日運動熱量消耗趨勢',
                          labels={'數值': '總消耗 (kcal)', '日期': '日期'},
                          markers=True)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
            # 顯示最近數據
            st.write("**最近 5 筆詳細紀錄：**")
            st.dataframe(df.tail(5), use_container_width=True, hide_index=True)
        else:
            st.info("尚無足夠的運動數據生成圖表。")
    else:
        st.info("請先新增紀錄以查看趨勢。")

# --- 二次確認清除區 ---
st.divider()
with st.expander("⚠️ 危險區域"):
    if st.button("🗑️ 刪除最後一筆紀錄"):
        if not df.empty:
            updated_df = df.iloc[:-1]
            conn.update(data=updated_df)
            st.success("已成功刪除！")
            st.rerun()
