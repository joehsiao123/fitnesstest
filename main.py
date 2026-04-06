import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("🍎 簡易健康紀錄器")

# 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有資料
data = conn.read(spreadsheet=st.secrets["GSHEET_URL"])
data = data.dropna(how="all") # 清除空行

# --- 輸入介面 ---
with st.form("record_form", clear_on_submit=True):
    date = st.date_input("日期", datetime.now())
    category = st.selectbox("類別", ["飲食 (kcal)", "運動 (min)"])
    item = st.text_input("內容 (例如: 雞腿便當 / 慢跑)")
    value = st.number_input("數值", min_value=0)
    
#

# --- 顯示最近 5 筆紀錄 ---
st.write("### 📝 最近紀錄")
st.table(data.tail(5))
