import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取（它會自動去 secrets 的 [connections.gsheets] 找 spreadsheet 網址）
df = conn.read(ttl=0)

# 更新
# conn.update(data=your_new_df)


    # 清理資料（移除全空的列）
    #df = df.dropna(how="all")
except Exception as e:
    st.error(f"連線異常: {e}")
    st.stop()

# --- 4. 側邊欄：新增紀錄表單 ---
st.sidebar.header("📝 新增紀錄")
with st.sidebar.form("input_form", clear_on_submit=True):
    date = st.date_input("日期", datetime.now())
    category = st.selectbox("分類", ["🥗 飲食", "💪 運動"])
    item = st.text_input("內容", placeholder="例如：雞胸肉、慢跑")
    value = st.number_input("數值 (kcal / min)", min_value=0, step=1)
    
    submit = st.form_submit_button("儲存到雲端")
    
    if submit:
        if item:
            # 建立新列
            new_data = pd.DataFrame([{
                "日期": date.strftime("%Y-%m-%d"),
                "項目": f"{category}: {item}",
                "數值": value
            }])
            
            # 合併舊資料與新資料
            updated_df = pd.concat([df, new_data], ignore_index=True)
            
            # 寫回 Google Sheets
            conn.update(spreadsheet=st.secrets["GSHEET_URL"], data=updated_df)
            st.sidebar.success("✅ 已成功儲存！")
            st.rerun() # 重新整理頁面以顯示新資料
        else:
            st.sidebar.warning("請填寫內容名稱")

# --- 5. 主頁面：數據呈現 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 歷史紀錄清單")
    if not df.empty:
        # 倒序顯示，讓最新的在上面
        st.dataframe(df.iloc[::-1], use_container_width=True)
    else:
        st.info("目前尚無資料，請從左側選單開始記錄！")

with col2:
    st.subheader("📊 快速統計")
    if not df.empty:
        # 計算今日總計
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_data = df[df['日期'] == today_str]
        
        total_kcal = today_data[today_data['項目'].str.contains("飲食")]['數值'].sum()
        total_mins = today_data[today_data['項目'].str.contains("運動")]['數值'].sum()
        
        st.metric("今日攝取", f"{total_kcal} kcal")
        st.metric("今日運動", f"{total_mins} min")
    else:
        st.write("暫無統計數據")
