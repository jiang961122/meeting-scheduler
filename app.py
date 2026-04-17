import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- 頁面設定 ---
st.set_page_config(page_title="會議統整大師-專業版", layout="centered")

# --- 1. 連接 Google Sheets ---
def connect_to_sheet():
    try:
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(creds)
        sh = client.open("會議投票資料庫") 
        try:
            ws_set = sh.worksheet("Settings")
            ws_vote = sh.worksheet("Votes")
        except:
            ws_set = sh.add_worksheet(title="Settings", rows="10", cols="2")
            ws_vote = sh.add_worksheet(title="Votes", rows="100", cols="20")
        return ws_set, ws_vote
    except Exception as e:
        st.error(f"資料庫連線失敗：{e}")
        return None, None

# --- 2. 核心功能函數 (增加讀取說明欄位) ---
def load_cloud_data():
    ws_set, ws_vote = connect_to_sheet()
    if not ws_set: return None
    
    settings = ws_set.get_all_values()
    # 確保 Settings 表至少有三行資料 (標題、說明、時段)
    if not settings or len(settings) < 3: return None
    
    title = settings[0][1]
    description = settings[1][1] # 新增：讀取說明
    slots = settings[2][1].split(',')
    
    votes_raw = ws_vote.get_all_records()
    votes_dict = {}
    for row in votes_raw:
        name = row.pop('姓名')
        votes_dict[name] = [str(v) == "1" for v in row.values()]
    
    return {"title": title, "description": description, "slots": slots, "votes": votes_dict}

# --- 3. 樣式 ---
st.markdown("""<style>.time-badge { background-color: #e6f3ff; color: #0068c9; padding: 4px 12px; border-radius: 16px; margin: 4px; display: inline-block; font-weight: 600; }</style>""", unsafe_allow_html=True)
green_check = "https://cdn-icons-png.flaticon.com/128/14025/14025310.png"
red_cross = "https://cdn-icons-png.flaticon.com/128/10308/10308565.png"

# --- 主程式邏輯 ---
st.title("📅 會議時間統整小幫手")

# === 側邊欄設計 ===
with st.sidebar:
    st.header("切換身分")
    user_mode = st.radio("選擇模式", ["👤 訪客模式", "👨‍💼 管理員模式"], horizontal=True, label_visibility="collapsed")
    
    is_admin = False
    if user_mode == "👨‍💼 管理員模式":
        admin_pw = st.text_input("請輸入密碼解鎖", type="password")
        if admin_pw == "1234":
            is_admin = True
            st.success("解鎖成功！")
            # 調整 1：刷新按鈕只在管理員成功登入後出現
            if st.button("🔄 刷新雲端最新資料"):
                st.session_state.cloud_data = load_cloud_data()
                st.rerun()
        elif admin_pw != "":
            st.error("密碼錯誤")

# 初始讀取資料
if 'cloud_data' not in st.session_state:
    st.session_state.cloud_data = load_cloud_data()

data = st.session_state.cloud_data

# === 分流邏輯 ===
if is_admin:
    tab1, tab2 = st.tabs(["🆕 建立新會議", "📊 查看結果"])
    
    with tab1:
        new_title = st.text_input("會議名稱", placeholder="請輸入會議名稱")
        # 調整 3：增加會議內容說明的輸入欄位
        new_desc = st.text_area("會議內容說明", placeholder="請輸入會議議程或注意事項...")
        
        st.divider()
        st.subheader("設定時段")
        col1, col2 = st.columns(2)
        with col1:
            pick_date = st.date_input("選擇日期")
        with col2:
            pick_times = st.multiselect("選擇時段", ["09:00","10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"])
        
        if 'temp_slots' not in st.session_state: st.session_state.temp_slots = []
        if st.button("➕ 加入候選時段"):
            for t in pick_times:
                s = f"{pick_date} {t}"
                if s not in st.session_state.temp_slots: st.session_state.temp_slots.append(s)
            st.session_state.temp_slots.sort()
            
      if st.session_state.temp_slots:
            st.markdown("#### 目前已選時段：")
            # 透過迴圈將每個時段變成 Markdown 的條列式項目
            for slot in st.session_state.temp_slots:
                st.markdown(f"* {slot}")
            
            st.write("") # 增加一點換行空白，讓畫面不擁擠
            
            if st.button("🚀 發布並覆蓋雲端舊活動", type="primary"):
                ws_set, ws_vote = connect_to_sheet()
                ws_set.clear()
                # 調整 3：將標題、說明、時段依序寫入 Google Sheets
                ws_set.update([["Title", new_title], ["Description", new_desc], ["Slots", ",".join(st.session_state.temp_slots)]])
                ws_vote.clear()
                ws_vote.append_row(["姓名"] + st.session_state.temp_slots)
                st.success("同步成功！")
                st.session_state.temp_slots = []
                st.session_state.cloud_data = load_cloud_data()
                st.rerun()

    with tab2:
        if data and data['votes']:
            st.header(data['title']) # 管理員也能看到標題
            df = pd.DataFrame(data['votes'], index=data['slots']).T
            st.write(df.style.format(lambda v: f'<img src="{green_check if v else red_cross}" width="20">').to_html(escape=False), unsafe_allow_html=True)
        else:
            st.info("尚無投票資料")

else:
    # 訪客投票介面
    if not data:
        st.warning("目前雲端沒有進行中的活動。")
    else:
        # 調整 2：直接呈現名稱，不加「會議：」
        st.header(data['title'])
        # 調整 3：在名稱下方顯示說明文字
        if data['description']:
            st.info(data['description'])
            
        st.divider()
        user_name = st.text_input("您的姓名")
        with st.form("vote_form"):
            st.write("請勾選您有空的時間：")
            user_choices = []
            for s in data['slots']:
                user_choices.append(st.checkbox(s))
            if st.form_submit_button("送出投票"):
                if user_name:
                    _, ws_vote = connect_to_sheet()
                    ws_vote.append_row([user_name] + [1 if c else 0 for c in user_choices])
                    st.success("投票已上傳雲端，謝謝您的參與！")
                    st.session_state.cloud_data = load_cloud_data()
                else:
                    st.error("請輸入姓名")
