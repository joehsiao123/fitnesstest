import streamlit as st
import datetime

st.title("🍎 飲食與運動記錄")

# 輸入介面
date = st.date_input("日期", datetime.date.today())
category = st.selectbox("類型", ["飲食", "運動"])
content = st.text_input("內容 (例如：雞胸肉 / 跑步 5km)")
value = st.number_input("數值 (大卡 / 分鐘)", min_value=0)

if st.button("送出記錄"):
    # 這裡建議搭配後端資料庫，初步測試可先顯示在網頁上
    st.success(f"已記錄：{date} {category} - {content} ({value})")
