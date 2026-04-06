import streamlit as st
from notion_client import Client
from datetime import datetime

# 1. 從 Secrets 讀取設定
notion = Client(auth=st.secrets["NOTION_TOKEN"])
database_id = st.secrets["NOTION_DATABASE_ID"]

st.set_page_config(page_title="iPad 健康日誌", page_icon="📝")
st.title("🍎 飲食與運動同步至 Notion")

# 2. 建立輸入表單
with st.form("health_form", clear_on_submit=True):
    date = st.date_input("日期", datetime.now())
    category = st.selectbox("類型", ["飲食", "運動"])
    item = st.text_input("項目名稱 (例如：雞胸肉 / 慢跑)")
    amount = st.number_input("數值 (大卡 / 分鐘)", min_value=0)
    
    submitted = st.form_submit_button("確認儲存")

    if submitted:
        try:
            # 3. 呼叫 Notion API 建立新頁面 (一筆資料)
            notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Name": {"title": [{"text": {"content": item}}]},
                    "Date": {"date": {"start": date.strftime("%Y-%m-%d")}},
                    "Category": {"select": {"name": category}},
                    "Amount": {"number": amount}
                }
            )
            st.success(f"✅ 已成功同步到 Notion！項目：{item}")
        except Exception as e:
            st.error(f"❌ 儲存失敗，錯誤訊息：{e}")
