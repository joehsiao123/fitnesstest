import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 配置區 ---
NOTION_TOKEN = "你的_INTEGRATION_TOKEN"
FOOD_DB_ID = "你的_飲食資料庫_ID"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# --- 函式：寫入資料到 Notion ---
def insert_food_record(name, calories, date):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": FOOD_DB_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": name}}]},
            "Calories": {"number": calories},
            "Date": {"date": {"start": date.strftime("%Y-%m-%d")}}
        }
    }
    res = requests.post(url, headers=headers, json=data)
    return res.status_code

# --- Streamlit UI 介面 ---
st.set_page_config(page_title="健身飲食紀錄器", layout="centered")

st.title("🍎 飲食與運動紀錄助手")
st.subheader("串連 Notion 的個人健康看板")

tab1, tab2 = st.tabs(["新增紀錄", "數據檢視"])

with tab1:
    st.write("### 📝 紀錄今日飲食")
    with st.form("food_form"):
        food_name = st.text_input("食物名稱", placeholder="例如：雞胸肉沙拉")
        calories = st.number_input("熱量 (kcal)", min_value=0, step=10)
        date = st.date_input("日期", datetime.now())
        
        submit = st.form_submit_button("送出至 Notion")
        
        if submit:
            if food_name:
                status = insert_food_record(food_name, calories, date)
                if status == 200:
                    st.success(f"成功記錄：{food_name}！")
                else:
                    st.error(f"寫入失敗，錯誤碼：{status}")
            else:
                st.warning("請輸入食物名稱")

with tab2:
    st.info("這裡可以串接 Notion Query API 來拉取歷史數據並顯示圖表。")
    # 提示：可以使用 requests.post(f"https://api.notion.com/v1/databases/{FOOD_DB_ID}/query")
