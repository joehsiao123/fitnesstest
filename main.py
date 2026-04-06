import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 頁面配置 ---
st.set_page_config(page_title="Fitness Pro", layout="wide", page_icon="💪")

# --- 核心連線 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0).dropna(how="all")
except Exception as e:
    st.error(f"連線失敗，請檢查 Secrets 設定：{e}")
    st.stop()

# --- 健身項目配置 (中文字卡與圖示) ---
EXERCISES = {
    "🏃 慢跑": 400,    # 每 30 分鐘估計消耗
    "🚴 單車": 300,
    "🏊 游泳": 500,
    "🏋️ 重訓": 250,
    "🧘 瑜珈": 150,
    "🏸 羽球": 350,
    "🥊 拳擊": 600,
    "🚶 散步": 100
}

# --- 標題 ---
st.title("💪 個人健康紀錄中心")

# --- UI 佈局 ---
col_form, col_stat = st.columns([3, 2])

with col_form:
    st.subheader("📝 快速新增")
    
    # 使用 Radio 製作視覺化卡路里選擇器 (水平排列適合 iPad)
    st.write("**1. 選擇健身項目**")
    selected_exercise = st.radio(
        "健身類別", 
        options=list(EXERCISES.keys()), 
        horizontal=True,
        label_visibility="collapsed"
    )
    
    with st.form("quick_add_form", clear_on_submit=True):
        f_date = st.date_input("日期", datetime.now())
        
        c1, c2 = st.columns(2)
        with c1:
            # 根據選擇的項目自動預填卡路里
            base_kcal = EXERCISES[selected_exercise]
            f_val = st.number_input("消耗卡路里 (kcal)", min_value=0, value=base_kcal)
        with c2:
            f_duration = st.number_input("運動時長 (分鐘)", min_value=0, value=30)
            
        f_note = st.text_input("補充筆記 (選填)", placeholder="例如：今天體感很好")
        
        submitted = st.form_submit_button("🔥 確認存入 Google Sheets", use_container_width=True)
        
        if submitted:
            with st.spinner("同步至雲端..."):
                try:
                    # 建立新資料
                    new_row = pd.DataFrame([{
                        "日期": f_date.strftime("%Y-%m-%d"),
                        "項目": f"{selected_exercise} ({f_duration}min)",
                        "數值": f_val,
                        "備註": f_note
                    }])
                    
                    # 合併並更新
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    
                    st.success(f"成功記錄 {selected_exercise}！消耗 {f_val} kcal")
                    st.balloons()
                    # 重新整理頁面顯示最新數據
                    st.rerun()
                except Exception as ex:
                    st.error(f"寫入失敗：{ex}")

with col_stat:
    st.subheader("📊 本週統計")
    # 簡易數據展示
    if not df.empty:
        # 確保數值欄位是數字
        df['數值'] = pd.to_numeric(df['數值'], errors='coerce')
        total_kcal = df['數值'].sum()
        st.metric("總計消耗卡路里", f"{int(total_kcal)} kcal", delta="Keep going!")
        
        st.divider()
        st.write("**最近 5 筆動態**")
        st.dataframe(df.tail(5), use_container_width=True, hide_index=True)
    else:
        st.info("尚無紀錄，開始你的第一次運動吧！")

# --- 底部視覺化卡片 ---
st.divider()
st.subheader("💡 健身建議 (參考)")
cols = st.columns(len(EXERCISES))
for i, (name, kcal) in enumerate(EXERCISES.items()):
    with cols[i]:
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:10px; padding:10px; text-align:center; background-color:#f9f9f9;">
            <h2 style="margin:0;">{name.split()[0]}</h2>
            <p style="margin:0; font-size:14px; color:#666;">{name.split()[1]}</p>
            <b style="color:#ff4b4b;">{kcal} kcal</b>
        </div>
        """, unsafe_allow_html=True)
