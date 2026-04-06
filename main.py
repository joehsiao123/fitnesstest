import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- Notion API 客戶端 ---
class NotionClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def add_food(self, db_id, name, calories, date):
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Calories": {"number": calories},
                "Date": {"date": {"start": date.strftime("%Y-%m-%d")}}
            }
        }
        return requests.post(url, headers=self.headers, json=payload)

    def add_workout(self, db_id, activity, duration, date):
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Activity": {"title": [{"text": {"content": activity}}]},
                "Duration (min)": {"number": duration},
                "Date": {"date": {"start": date.strftime("%Y-%m-%d")}}
            }
        }
        return requests.post(url, headers=self.headers, json=payload)

# --- 初始化 ---
st.set_page_config(page_title="Health Tracker", page_icon="💪")

# 從 Secrets 安全取得資訊
try:
    notion = NotionClient(st.secrets["NOTION_TOKEN"])
    FOOD_DB_ID = st.secrets["FOOD_DB_ID"]
    WORKOUT_DB_ID = st.secrets["WORKOUT_DB_ID"]
except KeyError:
    st.error("請在 .streamlit/secrets.toml 中設定 API 資訊！")
    st.stop()

# --- 主介面 ---
st.title("🏋️ 個人健康紀錄 App")
st.markdown("---")

# 使用側邊欄導覽
choice = st.sidebar.radio("選擇功能", ["🥗 飲食紀錄", "🏃 運動紀錄"])

if choice == "🥗 飲食紀錄":
    st.header("新增飲食內容")
    with st.form("food_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("食物名稱", placeholder="例如：雞胸肉便當")
            date = st.date_input("紀錄日期", datetime.now())
        with col2:
            cals = st.number_input("預估熱量 (kcal)", min_value=0, step=50)
        
        submitted = st.form_submit_button("儲存至 Notion")
        
        if submitted:
            if name:
                with st.spinner("正在同步至 Notion..."):
                    response = notion.add_food(FOOD_DB_ID, name, cals, date)
                    if response.status_code == 200:
                        st.success(f"✅ 已儲存：{name} ({cals} kcal)")
                    else:
                        st.error(f"儲存失敗：{response.text}")
            else:
                st.warning("請填寫食物名稱")

elif choice == "🏃 運動紀錄":
    st.header("新增運動項目")
    with st.form("workout_form", clear_on_submit=True):
        activity = st.text_input("運動項目", placeholder="例如：慢跑、重訓")
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("時長 (分鐘)", min_value=1, step=5)
        with col2:
            date = st.date_input("紀錄日期", datetime.now())
            
        submitted = st.form_submit_button("儲存至 Notion")
        
        if submitted:
            if activity:
                with st.spinner("正在傳送數據..."):
                    response = notion.add_workout(WORKOUT_DB_ID, activity, duration, date)
                    if response.status_code == 200:
                        st.success(f"🔥 太棒了！已完成 {duration} 分鐘的 {activity}")
                    else:
                        st.error(f"儲存失敗：{response.text}")
            else:
                st.warning("請填寫運動項目")

# 頁尾資訊
st.sidebar.markdown("---")
st.sidebar.info("💡 提示：輸入完後資料會即時同步到你的 Notion 資料庫。")
