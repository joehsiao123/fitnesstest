import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("🍎 飲食與運動記錄器")

# 1. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 安全讀取資料
try:
    # 先不管欄位，把整張表讀進來
    existing_data = conn.read(worksheet="Sheet1", ttl=0) # ttl=0 代表不快取，每次都抓最新的
    existing_data = existing_data.dropna(how="all")
except Exception as e:
    # 如果表單是完全空白的，就建立一個預設的空表格
    existing_data = pd.DataFrame(columns=["date", "category", "item", "amount"])

# 3. 輸入表單
with st.form("record_form", clear_on_submit=True):
    date = st.date_input("日期", datetime.now())
    category = st.radio("類別", ["飲食", "運動"], horizontal=True)
    item = st.text_input("內容 (如：煎鮭魚 / 慢跑 30min)")
    amount = st.number_input("數值 (大卡 / 分鐘)", min_value=0)
    
    submit = st.form_submit_button("儲存記錄")
    
    if submit:
        # 建立新資料
        new_data = pd.DataFrame([{
            "date": date.strftime("%Y-%m-%d"),
            "category": category,
            "item": item,
            "amount": amount
        }])
        
        # 合併新舊資料
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 寫回 Google Sheets
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ 資料已成功同步至 Google Sheets！")
        st.balloons() # 成功時噴發氣球慶祝一下

# 4. 顯示歷史紀錄
st.subheader("📊 歷史記錄")
st.dataframe(existing_data.tail(10))
