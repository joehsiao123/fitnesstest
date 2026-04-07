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

# --- 數據庫配置 (熱門項目與預估值) ---
# 飲食：參考台灣常見外食熱量
FOOD_ITEMS = {
    "🍱 便當/定食": 750,
    "🍜 湯麵/拉麵": 600,
    "🥪 三明治/飯糰": 350,
    "🥗 沙拉/輕食": 250,
    "🥟 水餃/鍋貼": 500,
    "🍔 漢堡/速食": 800,
    "☕ 咖啡/拿鐵": 150,
    "🧋 珍珠奶茶": 650,
    "🍎 水果/點心": 150,
    "🥩 火鍋/燒肉": 900
}

# 運動：每 30 分鐘消耗量
WORKOUT_ITEMS = {
    "🏃 慢跑": 300,
    "🏋️ 重訓": 200,
    "🧘 瑜珈/伸展": 120,
    "🚴 單車/飛輪": 250,
    "🏊 游泳": 400,
    "🚶 散步": 100
}

# --- 標題 ---
st.title("💪 飲食與運動全能紀錄")

# --- UI 佈局 ---
col_form, col_view = st.columns([3, 2])

with col_form:
    st.subheader("📝 快速新增紀錄")
    
    # 1. 大類別切換
    log_type = st.radio("想要記錄什麼？", ["🥗 飲食紀錄", "🏃 運動紀錄"], horizontal=True)
    
    # 2. 根據大類別顯示對應字卡
    current_items = FOOD_ITEMS if "飲食" in log_type else WORKOUT_ITEMS
    
    st.write("**點選常用項目：**")
    selected_item = st.selectbox(
        "選擇項目", 
        options=list(current_items.keys()),
        label_visibility="collapsed"
    )
    
    # 3. 表單填寫
    with st.form("entry_form", clear_on_submit=True):
        f_date = st.date_input("日期", datetime.now())
        
        c1, c2 = st.columns(2)
        with c1:
            # 自動連動預設值
            default_val = current_items[selected_item]
            f_val = st.number_input("熱量 (kcal)", min_value=0, value=default_val)
        with c2:
            f_label = "份量/備註" if "飲食" in log_type else "時長(分鐘)"
            f_note = st.text_input(f_label, placeholder="選填")
            
        submitted = st.form_submit_button("🔥 確認存入 Google Sheets", use_container_width=True)
        
        if submitted:
            try:
                # 統一寫入格式
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
                st.balloons()
                st.rerun()
            except Exception as ex:
                st.error(f"寫入失敗：{ex}")

with col_view:
    st.subheader("📊 今日概覽")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if not df.empty:
        # 篩選今日數據
        today_df = df[df['日期'] == today_str].copy()
        today_df['數值'] = pd.to_numeric(today_df['數值'], errors='coerce')
        
        in_kcal = today_df[today_df['類別'].str.contains("飲食")]['數值'].sum()
        out_kcal = today_df[today_df['類別'].str.contains("運動")]['數值'].sum()
        
        st.metric("今日攝取 (In)", f"{int(in_kcal)} kcal")
        st.metric("今日消耗 (Out)", f"{int(out_kcal)} kcal")
        st.metric("淨值", f"{int(in_kcal - out_kcal)} kcal", delta_color="inverse")
        
        st.divider()
        st.write("**最近紀錄**")
        st.dataframe(df.tail(8), use_container_width=True, hide_index=True)
    else:
        st.info("尚無數據")

# --- 視覺化字卡展示 ---
st.divider()
st.subheader("💡 常用項目快速參考")
display_cols = st.columns(5)
all_items = list(FOOD_ITEMS.items())[:10] # 顯示前10項飲食

for i, (name, kcal) in enumerate(all_items):
    with display_cols[i % 5]:
        st.markdown(f"""
        <div style="border:1px solid #eee; border-radius:10px; padding:10px; text-align:center; margin-bottom:10px;">
            <div style="font-size:24px;">{name.split()[0]}</div>
            <div style="font-weight:bold;">{name.split()[1]}</div>
            <div style="color:#ff4b4b;">{kcal} kcal</div>
        </div>
        """, unsafe_allow_html=True)
