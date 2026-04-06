import streamlit as st
import requests
from datetime import datetime
import time

# --- 1. 從 Secrets 取得金鑰 ---
try:
    NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
    FOOD_DB_ID = st.secrets["FOOD_DB_ID"]
    WORKOUT_DB_ID = st.secrets["WORKOUT_DB_ID"]
except Exception as e:
    st.error("❌ Secrets 載入失敗，請檢查 .streamlit/secrets.toml")
    st.stop()

# --- 2. 日誌紀錄系統 ---
if "logs" not in st.session_state:
    st.session_state.logs = []

def add_log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    st.session_state.logs.append(log_entry)
    # 只保留最後 10 筆紀錄避免畫面太長
    if len(st.session_state.logs) > 10:
        st.session_state.logs.pop(0)

# --- 3. Notion API 傳送函式 ---
def post_to_notion(db_id, properties, label):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    payload = {"parent": {"database_id": db_id}, "properties": properties}
    
    add_log(f"嘗試發送數據到 {label} 資料庫...")
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            add_log(f"✅ 成功寫入 {label}！", "SUCCESS")
        else:
            add_log(f"❌ 失敗！狀態碼: {res.status_code}，訊息: {res.text}", "ERROR")
        return res
    except Exception as e:
        add_log(f"🚨 發生異常: {str(e)}", "CRITICAL")
        return None

# --- 4. Streamlit UI 介面 ---
st.set_page_config(page_title="Health Tracker & Debugger", layout="wide")

st.title("💪 健康紀錄小助手 (含即時 Log)")

# 建立左右兩欄：左邊輸入，右邊顯示 Log
col_input, col_log = st.columns([2, 1])

with col_input:
    tab1, tab2 = st.tabs(["🥗 飲食紀錄", "🏃 運動紀錄"])

    with tab1:
        with st.form("food_form", clear_on_submit=True):
            name = st.text_input("食物名稱")
            cals = st.number_input("熱量 (kcal)", min_value=0)
            date = st.date_input("日期", datetime.now(), key="f_date")
            if st.form_submit_button("送出飲食紀錄"):
                if name:
                    props = {
                        "Name": {"title": [{"text": {"content": name}}]},
                        "Calories": {"number": cals},
                        "Date": {"date": {"start": date.strftime("%Y-%m-%d")}}
                    }
                    post_to_notion(FOOD_DB_ID, props, "飲食")
                else:
                    st.warning("請填寫名稱")

    with tab2:
        with st.form("workout_form", clear_on_submit=True):
            act = st.text_input("運動項目")
            mins = st.number_input("時長 (分鐘)", min_value=1)
            date = st.date_input("日期", datetime.now(), key="w_date")
            if st.form_submit_button("送出運動紀錄"):
                if act:
                    props = {
                        "Activity": {"title": [{"text": {"content": act}}]},
                        "Duration (min)": {"number": mins},
                        "Date": {"date": {"start": date.strftime("%Y-%m-%d")}}
                    }
                    post_to_notion(WORKOUT_DB_ID, props, "運動")
                else:
                    st.warning("請填寫項目")

# --- 5. 右側 Log 顯示區 ---
with col_log:
    st.subheader("📜 執行日誌")
    if st.button("清除日誌"):
        st.session_state.logs = []
        st.rerun()
    
    # 使用程式碼區塊顯示 Log，看起來更專業
    log_text = "\n".join(st.session_state.logs[::-1]) # 倒序顯示，最新的在上面
    st.code(log_text if log_text else "等待操作中...", language="text")

    # 針對先前的 401 錯誤提供快速檢查
    if any("401" in log for log in st.session_state.logs):
        st.error("偵測到 401 錯誤！請檢查：\n1. Notion 頁面是否已『連接』Integration\n2. Token 是否正確")
