import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("🍎 飲食運動永久記錄器")

# 1. 建立 Google Sheets 連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 讀取現有資料 (為了顯示歷史紀錄)
existing_data = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3], ttl=5)
existing_data = existing_data.dropna(how="all")

# 3. 輸入介面
with st.form("record_form"):
    date = st.date_input("日期", datetime.now())
    category = st.selectbox("類別", ["飲食", "運動"])
    item = st.text_input("內容")
    amount = st.number_input("數值", min_value=0)
    submit = st.form_submit_button("儲存到雲端")

    if submit:
        # 建立新的一列資料
        new_data = pd.DataFrame([{
            "date": date.strftime("%Y-%m-%d"),
            "category": category,
            "item": item,
            "amount": amount
        }])
        
        # 合併舊資料與新資料
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 寫回 Google Sheets
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ 資料已同步至 Google Sheets！")

# 4. 顯示最近的記錄
st.subheader("歷史記錄")
st.dataframe(existing_data.tail(10))
