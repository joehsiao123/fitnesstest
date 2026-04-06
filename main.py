import streamlit as st
from notion_client import Client

# 在 Streamlit Secrets 設定 Token 和 Database ID
notion = Client(auth=st.secrets["NOTION_TOKEN"])
database_id = st.secrets["NOTION_DATABASE_ID"]

st.title("🍎 Notion 健康日誌同步器")

with st.form("notion_form"):
    date = st.date_input("日期")
    item = st.text_input("內容")
    cat = st.selectbox("類別", ["飲食", "運動"])
    val = st.number_input("數值", min_value=0)
    
    if st.form_submit_button("傳送到 Notion"):
        # 建立 Notion 資料庫的一行
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "項目": {"title": [{"text": {"content": item}}]},
                "日期": {"date": {"start": date.strftime("%Y-%m-%d")}},
                "類別": {"select": {"name": cat}},
                "數值": {"number": val}
            }
        )
        st.success("✅ 資料已存入 Notion！")
