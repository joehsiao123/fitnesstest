import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 頁面配置 ---
st.set_page_config(page_title="Health Log Pro", layout="wide", page_icon="🥗")

# --- 核心連線 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0).dropna(how="all")
except Exception as e:
    st.error(f"連線失敗：{e}")
    st.stop()

# --- 數據庫配置 ---
FOOD_ITEMS = {
    "🍱 便當/定食": 750, "🍜 湯麵/拉麵": 600, "🥪 三明治/飯糰": 350,
    "🥗 沙拉/輕食": 250, "🥟 水餃/鍋貼": 500, "🍔 漢堡/速食": 800,
    "☕ 咖啡/拿鐵": 150, "🧋 珍珠奶茶": 650, "🍎 水果/點心": 150, "🥩 火鍋/燒肉": 900
}

WORKOUT_ITEMS = {
    "🏃 慢跑": 300, "🏋️ 重訓": 200, "🧘 瑜珈/伸展": 120,
    "🚴 單車/飛輪": 250, "🏊 游泳": 400, "🚶 散步": 100
}

# --- 標題 ---
st.title("💪 飲食與運動全能紀錄")

# --- UI 佈局 ---
col_form, col_view = st.columns([3, 2])

with col_form:
    st.subheader("📝 快速新增紀錄")
    
    log_type = st.radio("想要記錄什麼？", ["🥗 飲食紀錄", "🏃 運動紀錄"], horizontal=True)
    current_items = FOOD_ITEMS if "飲食" in log_type else WORKOUT_ITEMS
    
    selected_item = st.selectbox("選擇項目", options=list(current_items.keys()))
    
    with st.form("entry_form", clear_on_submit=True):
        f_date = st.date_input("日期", datetime.now())
        c1, c2 = st.columns(2)
        with c1:
            f_val = st.number_input("熱量 (kcal)", min_value=0, value=current_items[selected_item])
        with c2:
            f_note = st.text_input("份量/時長備註", placeholder="選填")
            
        submitted = st.form_submit_button("🔥 確認存入 Google Sheets", use_container_width=True)
        
        if submitted:
            try:
                new_row = pd.DataFrame([{
                    "日期": f_date.strftime("%Y-%m-%d"),
                    "類別": log_type,
                    "項目": selected_item,
                    "數值": f_val,
                    "備註": f_note
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"已記錄：{selected_item}")
                st.rerun()
            except Exception as ex:
                st.error(f"寫入失敗：{ex}")

    # --- 新增：管理區域 (含二次確認清除功能) ---
    st.divider()
    st.subheader("⚙️ 紀錄管理")
    m_col1, m_col2 = st.columns(2)

    with m_col1:
        # 使用 popover 製作優雅的二次確認
        with st.popover("🗑️ 刪除最後一筆紀錄", use_container_width=True):
            st.warning("確定要刪除雲端試算表中的『最後一筆』紀錄嗎？此動作無法復原。")
            if st.button("確認刪除", type="primary"):
                if not df.empty:
                    try:
                        # 移除最後一列並更新
                        updated_df = df.iloc[:-1]
                        conn.update(data=updated_df)
                        st.success("最後一筆紀錄已清除！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"刪除失敗：{e}")
                else:
                    st.info("目前沒有紀錄可刪除。")

    with m_col2:
        # 清除畫面上目前的輸入暫存 (Session State)
        if st.button("🧹 清除畫面填寫內容", use_container_width=True):
            st.rerun() # 簡單透過重新整理來達成清除效果

with col_view:
    st.subheader("📊 今日概覽")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if not df.empty:
        today_df = df[df['日期'] == today_str].copy()
        today_df['數值'] = pd.to_numeric(today_df['數值'], errors='coerce')
        
        in_kcal = today_df[today_df['類別'].str.contains("飲食")]['數值'].sum()
        out_kcal = today_df[today_df['類別'].str.contains("運動")]['數值'].sum()
        
        st.metric("今日攝取 (In)", f"{int(in_kcal)} kcal")
        st.metric("今日消耗 (Out)", f"{int(out_kcal)} kcal")
        
        st.divider()
        st.write("**最近紀錄**")
        st.dataframe(df.tail(8), use_container_width=True, hide_index=True)
    else:
        st.info("尚無數據")
