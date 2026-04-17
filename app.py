import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# --- 頁面設定 ---
st.set_page_config(page_title="會議統整大師-雲端版", layout="centered")

# --- 1. 連接 Google Sheets (使用 Streamlit Secrets) ---
def connect_to_sheet():
    try:
        # 這裡會讀取我們稍後在 Streamlit Cloud 設定的 Secrets
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(creds)
        sh = client.open("會議投票資料庫") # 這裡必須跟您的試算表名稱一模一樣
        
        # 取得或初始化分頁
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

# --- 2. 核心功能函數 ---
def load_cloud_data():
    ws_set, ws_vote = connect_to_sheet()
    if not ws_set: return None
    
    settings = ws_set.get_all_values()
    if not settings or len(settings) < 2: return None
    
    title = settings[0][1]
    slots = settings[1][1].split(',')
    
    votes_raw = ws_vote.get_all_records()
    votes_dict = {}
    for row in votes_raw:
        name = row.pop('姓名')
        votes_dict[name] = [str(v) == "1" for v in row.values()]
    
    return {"title": title, "slots": slots, "votes": votes_dict}

# --- 3. 樣式與圖片 ---
st.markdown("""<style>.time-badge { background-color: #e6f3ff; color: #0068c9; padding: 4px 12px; border-radius: 16px; margin: 4px; display: inline-block; font-weight: 600; }</style>""", unsafe_allow_html=True)
green_check = "https://cdn-icons-png.flaticon.com/128/14025/14025310.png"
red_cross = "https://cdn-icons-png.flaticon.com/128/10308/10308565.png"

# --- 主程式 ---
st.title("📅 會議時間統整小幫手")

# === 側邊欄設計 ===
with st.sidebar:
    st.header("切換身分")
    # 使用水平排列的 radio 製作兩個切換按鈕
    user_mode = st.radio(
        "選擇模式", 
        ["👤 訪客模式", "👨‍💼 管理員模式"], 
        horizontal=True, 
        label_visibility="collapsed" # 隱藏標題讓畫面更簡潔
    )
    
    is_admin = False
    if user_mode == "👨‍💼 管理員模式":
        admin_pw = st.text_input("請輸入密碼解鎖", type="password")
        if admin_pw == "1234":
            is_admin = True
            st.success("解鎖成功！")
        elif admin_pw != "":
            st.error("密碼錯誤")
            
    st.divider() # 加入一條灰色分隔線
    
    if st.button("🔄 刷新雲端資料"):
        st.session_state.cloud_data = load_cloud_data()

# === 初始讀取 ===
if 'cloud_data' not in st.session_state:
    st.session_state.cloud_data = load_cloud_data()

data = st.session_state.cloud_data

# === 分流邏輯 ===
# 將原本的 if admin_pw == "1234": 改成 if is_admin:
if is_admin:
    tab1, tab2 = st.tabs(["🆕 建立新會議", "📊 查看結果"])
    
    with tab1:
        new_title = st.text_input("會議名稱")
        pick_date = st.date_input("日期")
        pick_times = st.multiselect("時段", ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"])
        
        if 'temp_slots' not in st.session_state: st.session_state.temp_slots = []
        if st.button("➕ 加入清單"):
            for t in pick_times:
                s = f"{pick_date} {t}"
                if s not in st.session_state.temp_slots: st.session_state.temp_slots.append(s)
            st.write("目前選取：", st.session_state.temp_slots)
            
        if st.button("🚀 發布並覆蓋雲端舊活動", type="primary"):
            ws_set, ws_vote = connect_to_sheet()
            ws_set.clear()
            ws_set.update([["Title", new_title], ["Slots", ",".join(st.session_state.temp_slots)]])
            ws_vote.clear()
            ws_vote.append_row(["姓名"] + st.session_state.temp_slots)
            st.success("同步成功！所有人現在都能看到新活動了。")
            st.session_state.cloud_data = load_cloud_data()

    with tab2:
        if data and data['votes']:
            df = pd.DataFrame(data['votes'], index=data['slots']).T
            st.write("### 投票明細")
            # 渲染您的表格樣式... (略，維持原樣)
            st.write(df.style.format(lambda v: f'<img src="{green_check if v else red_cross}" width="20">').to_html(escape=False), unsafe_allow_html=True)
        else:
            st.info("尚無投票資料")

else:
    # 訪客投票介面
    if not data:
        st.warning("目前沒有進行中的活動。")
    else:
        st.header(f"會議：{data['title']}")
        user_name = st.text_input("您的姓名")
        with st.form("vote_form"):
            user_choices = []
            for s in data['slots']:
                user_choices.append(st.checkbox(s))
            if st.form_submit_button("送出投票"):
                if user_name:
                    _, ws_vote = connect_to_sheet()
                    ws_vote.append_row([user_name] + [1 if c else 0 for c in user_choices])
                    st.success("投票已上傳雲端！")
                    st.session_state.cloud_data = load_cloud_data()
                else:
                    st.error("請輸入姓名")
