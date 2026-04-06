import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("🍎 簡易健康紀錄器")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有資料
data = conn.read(spreadsheet=st.secrets["GSHEET_URL"], usecols=[0, 1, 2])
data = data.dropna(how="all") # 清除空行

# --- 輸入介面 ---
with st.form("record_form", clear_on_submit=True):
    date = st.date_input("日期", datetime.now())
    category = st.selectbox("類別", ["飲食 (kcal)", "運動 (min)"])
    item = st.text_input("內容 (例如: 雞腿便當 / 慢跑)")
    value = st.number_input("數值", min_value=0)
    
    if st.form_submit_button("儲存紀錄"):
        # 建立新資料列
        new_row = pd.DataFrame([{
            "日期": date.strftime("%Y-%m-%d"),
            "項目": f"[{category}] {item}",
            "數值": value
        }])
        
        # 合併並更新到 Google Sheets
        updated_df = pd.concat([data, new_row], ignore_index=True)
        conn.update(spreadsheet=st.secrets["GSHEET_URL"], data=updated_df)
        st.success("✅ 紀錄已存入 Google 表格！")
        st.rerun()

# --- 顯示最近 5 筆紀錄 ---
st.write("### 📝 最近紀錄")
st.table(data.tail(5))
