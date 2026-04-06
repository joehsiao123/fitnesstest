import streamlit as st
from streamlit_gsheets import GSheetsConnection

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # 讀取資料
    df = conn.read(
        spreadsheet=st.secrets["GSHEET_URL"],
        ttl=0  # 禁用快取，確保即時讀取
    )
    
    if df.empty:
        st.warning("表格目前是空的！請先在 Google Sheet 第一列填入標題（例如：日期, 項目, 數值）")
    else:
        st.write("### 成功讀取資料：")
        st.dataframe(df)

except Exception as e:
    st.error(f"❌ 讀取失敗。請確認 secrets.toml 中的 GSHEET_URL 是否正確。")
    st.info(f"詳細錯誤訊息: {e}")
