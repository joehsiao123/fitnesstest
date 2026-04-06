import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 頁面配置 ---
st.set_page_config(page_title="Fitness Log", layout="wide")

# --- 日誌系統 ---
if "logs" not in st.session_state:
    st.session_state.logs = []

def add_log(message, type="INFO"):
    time_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{time_str}] {type}: {message}")
    if len(st.session_state.logs) > 15:
        st.session_state.logs.pop(0)

# --- 標題 ---
st.title("💪 個人健康紀錄 App (GSheet 版)")

# --- 建立連線 ---
# 套件會自動讀取 secrets 中的 [connections.gsheets] 區塊
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    # 移除空行
    df = df.dropna(how="all")
except Exception as e:
    st.error(f"連線失敗：{e}")
    st.stop()

# --- UI 佈局 ---
col_form, col_log = st.columns([2, 1])

with col_form:
    st.subheader("📝 新增紀錄")
    with st.form("main_form", clear_on_submit=True):
        f_date = st.date_input("日期", datetime.now())
        f_cat = st.selectbox("類別", ["🥗 飲食", "🏃 運動"])
        f_item = st.text_input("內容 (例如：雞腿便當 / 游泳)")
        f_val = st.number_input("數值 (kcal / 分鐘)", min_value=0)
        
        submitted = st.form_submit_button("確認儲存")
        
        if submitted:
            if f_item:
                add_log(f"正在嘗試寫入: {f_item}...")
                try:
                    # 建立新資料列
                    new_row = pd.DataFrame([{
                        "日期": f_date.strftime("%Y-%m-%d"),
                        "項目": f"{f_cat}: {f_item}",
                        "數值": f_val
                    }])
                    
                    # 合併資料並寫回
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    
                    add_log("✅ 寫入成功！", "SUCCESS")
                    st.success("資料已儲存！")
                    st.rerun()
                except Exception as ex:
                    add_log(f"❌ 寫入失敗: {ex}", "ERROR")
                    st.error(f"寫入出錯：{ex}")
            else:
                st.warning("請填寫內容標題")

    st.divider()
    st.subheader("📋 最近紀錄")
    st.dataframe(df.tail(10), use_container_width=True)

with col_log:
    st.subheader("📜 執行日誌")
    if st.button("清除日誌"):
        st.session_state.logs = []
        st.rerun()
    
    # 倒序顯示最新的 Log
    log_content = "\n".join(st.session_state.logs[::-1])
    st.code(log_content if log_content else "等待操作中...", language="text")

    st.info("💡 提示：若寫入失敗，請確認 Service Account 已被加入表格的『編輯者』共用名單。")
