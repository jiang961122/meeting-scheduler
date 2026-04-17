import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- 設定頁面 ---
st.set_page_config(page_title="會議時間統整大師", layout="centered")

# --- 1. 連接 Google Sheets 函數 ---
def get_gspread_client():
    # 從 Streamlit Secrets 讀取憑證
    creds = st.secrets["gcp_service_account"]
    # 進行授權
    return gspread.service_account_from_dict(creds)

def get_worksheet():
    client = get_gspread_client()
    # 【請修改處】請填入您的 Google 試算表名稱 (或是 URL)
    # 確保您已經把試算表「共用」給 JSON 裡面的 client_email 了
    sh = client.open("會議投票資料庫") 
    
    # 取得或建立工作表
    try:
        ws_settings = sh.worksheet("Settings")
        ws_votes = sh.worksheet("Votes")
    except:
        # 如果找不到就建立
        ws_settings = sh.add_worksheet(title="Settings", rows="100", cols="20")
        ws_votes = sh.add_worksheet(title="Votes", rows="100", cols="20")
    return ws_settings, ws_votes

# --- 2. 資料讀寫函數 ---
def load_event_data():
    try:
        ws_settings, ws_votes = get_worksheet()
        settings = ws_settings.get_all_values()
        if not settings: return None
        
        title = settings[0][1]
        slots = settings[1][1].split(',')
        
        votes_data = ws_votes.get_all_records()
        votes_dict = {}
        for row in votes_data:
            name = row.pop('姓名')
            # 將 1/0 轉回 True/False
            votes_dict[name] = [val == '1' for val in row.values()]
            
        return {'title': title, 'slots': slots, 'votes': votes_dict}
    except Exception as e:
        return None

def save_new_event(title, slots):
    ws_settings, ws_votes = get_worksheet()
    ws_settings.clear()
    ws_settings.update([['Title', title], ['Slots', ",".join(slots)]])
    ws_votes.clear()
    # 建立 Votes 的標題列
    header = ['姓名'] + slots
    ws_votes.append_row(header)

def submit_vote(name, selections, slots):
    _, ws_votes = get_worksheet()
    # 將 True/False 轉為 1/0 存檔
    row = [name] + [1 if s else 0 for s in selections]
    ws_votes.append_row(row)

# --- CSS 樣式 (您的版本) ---
st.markdown("""
<style>
    .time-badge { background-color: #e6f3ff; color: #0068c9; padding: 4px 12px; border-radius: 16px; border: 1px solid #cce5ff; margin: 4px; display: inline-block; font-size: 0.9em; font-weight: 600; }
    .date-header { font-size: 1.1em; font-weight: bold; color: #333; margin-top: 10px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

green_check_img = "https://cdn-icons-png.flaticon.com/128/14025/14025310.png"
red_cross_img = "https://cdn-icons-png.flaticon.com/128/10308/10308565.png"

# --- 初始化從 Google Sheets 讀取資料 ---
if 'db_data' not in st.session_state:
    st.session_state.db_data = load_event_data()

# ==========================================
# === 主介面邏輯 ===
# ==========================================

st.title("會議時間統整小幫手 🚀")

with st.sidebar:
    st.header("⚙️ 管理員設定")
    admin_password = st.text_input("輸入密碼進入管理模式", type="password")
    is_admin = (admin_password == "1234")
    if st.button("🔄 重新整理資料"):
        st.session_state.db_data = load_event_data()
        st.rerun()

# 根據是否有資料顯示頁面
if is_admin:
    tab1, tab2, tab3 = st.tabs(["1. 建立會議", "2. 投票頁面", "3. 統計結果"])
    
    with tab1:
        st.header("步驟一：設定會議名稱")
        title = st.text_input("會議名稱", placeholder="例如：Q1 產品規劃會議")
        
        st.header("步驟二：新增候選時段")
        col1, col2 = st.columns(2)
        with col1:
            pick_date = st.date_input("選擇日期", min_value=datetime.today())
        with col2:
            pick_times = st.multiselect("選擇時段", ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"])
        
        if 'temp_slots' not in st.session_state: st.session_state.temp_slots = []
        if st.button("➕ 加入候選清單"):
            for t in pick_times:
                s = f"{pick_date} {t}"
                if s not in st.session_state.temp_slots: st.session_state.temp_slots.append(s)
            st.session_state.temp_slots.sort()

        if st.session_state.temp_slots:
            st.write(st.session_state.temp_slots)
            if st.button("🚀 確認發布並寫入資料庫", type="primary"):
                save_new_event(title, st.session_state.temp_slots)
                st.session_state.db_data = load_event_data()
                st.success("活動已發布至雲端！")
    
    with tab2:
        # 顯示投票邏輯 (下同)
        pass 
    
    with tab3:
        # 顯示結果邏輯 (下同)
        pass

else:
    # 訪客模式
    data = st.session_state.db_data
    if not data:
        st.info("目前沒有進行中的活動，請聯繫主辦人。")
    else:
        st.header(f"會議：{data['title']}")
        voter_name = st.text_input("您的姓名")
        with st.form("vote_form"):
            selections = []
            for slot in data['slots']:
                selections.append(st.checkbox(slot))
            if st.form_submit_button("送出投票"):
                if voter_name:
                    submit_vote(voter_name, selections, data['slots'])
                    st.success("投票成功！")
                    st.session_state.db_data = load_event_data()
                else:
                    st.error("請輸入姓名")
