import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# --- 設定頁面 ---
st.set_page_config(page_title="會議時間統整大師", layout="centered")

# --- CSS 美化樣式 (您的版本) ---
st.markdown("""
<style>
    .time-badge {
        background-color: #e6f3ff;
        color: #0068c9;
        padding: 4px 12px;
        border-radius: 16px;
        border: 1px solid #cce5ff;
        margin: 4px;
        display: inline-block;
        font-size: 0.9em;
        font-weight: 600;
    }
    .date-header {
        font-size: 1.1em;
        font-weight: bold;
        color: #333;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .st-emotion-cache-1v0mbdj {
        width: 100%;
        overflow: auto;
    }
</style>
""", unsafe_allow_html=True)

# --- 載入並編碼圖片 (您的新連結) ---
green_check_img = "https://cdn-icons-png.flaticon.com/128/14025/14025310.png"
red_cross_img = "https://cdn-icons-png.flaticon.com/128/10308/10308565.png"

# --- 邏輯函數 ---
def reset_time_selection():
    st.session_state.pick_times = []

# --- 初始化 Session State ---
if 'event_data' not in st.session_state:
    st.session_state.event_data = {'title': '', 'slots': [], 'votes': {}}

if 'temp_slots' not in st.session_state:
    st.session_state.temp_slots = []

# ==========================================
# === 功能函數封裝區 ===
# ==========================================

def show_voting_page():
    """顯示投票介面 (您的 Tab 2 邏輯)"""
    st.header("填寫有空的時間")
    current_title = st.session_state.event_data['title']
    current_slots = st.session_state.event_data['slots']
    
    if not current_title:
        st.warning("👈 目前沒有進行中的會議 (請聯絡主辦人建立)。")
    else:
        st.subheader(f"會議：{current_title}")
        voter_name = st.text_input("您的姓名")
        st.write("請勾選您有空的時間：")
        
        with st.form("voting_form"):
            current_date_group = ""
            selections = []
            for slot in current_slots:
                date_part, time_part = slot.split(' ', 1)
                if date_part != current_date_group:
                    st.markdown(f"**📅 {date_part}**")
                    current_date_group = date_part
                is_selected = st.checkbox(f"{time_part}", key=slot)
                selections.append(is_selected)
            
            st.write("---")
            submit = st.form_submit_button("送出投票", type="primary")
            
            if submit:
                if voter_name:
                    st.session_state.event_data['votes'][voter_name] = selections
                    st.success(f"{voter_name}，您的投票已記錄！")
                else:
                    st.error("請輸入姓名。")

def show_results_page():
    """顯示統計結果介面 (您的 Tab 3 邏輯)"""
    st.header("統計結果")
    votes_dict = st.session_state.event_data['votes']
    slots = st.session_state.event_data['slots']
    
    if not votes_dict:
        st.info("尚無人投票。")
    else:
        df = pd.DataFrame(votes_dict, index=slots).T
        
        # 1. 定義背景顏色的函數 (您的設定：全灰底 #F0F0F0)
        def highlight_bg(val):
            color = '#F0F0F0' if val else '#F0F0F0' 
            return f'background-color: {color}'

        # 2. 定義顯示圖片的函數 (使用您的圖片變數)
        def show_images(val):
            if val:
                return f'<div style="text-align:center"><img src="{green_check_img}" width="24" /></div>'
            else:
                return f'<div style="text-align:center"><img src="{red_cross_img}" width="24" /></div>'

        st.write("### 投票明細")
        
        # 3. 應用樣式並渲染
        st.write(
            df.style
            .map(highlight_bg)  # 應用背景色
            .format(show_images) # 應用圖片
            .to_html(escape=False), 
            unsafe_allow_html=True
        )
        
        # 統計每個時段的總得票數
        vote_counts = df.sum(axis=0)
        best_slot = vote_counts.idxmax()
        max_votes = vote_counts.max()
        
        st.divider()
        st.subheader("🏆 最佳時段推薦")
        st.success(f"目前最佳時段是： **{best_slot}**，共有 **{max_votes}** 人有空。")

# ==========================================
# === 主程式邏輯 (權限控制) ===
# ==========================================

st.title("會議時間統整小幫手")

# --- 側邊欄：權限控制 ---
with st.sidebar:
    st.header("⚙️ 管理員設定")
    admin_password = st.text_input("輸入密碼進入管理模式", type="password")
    
    is_admin = False
    if admin_password == "1234":
        is_admin = True
        st.success("已解鎖管理員模式")
    else:
        st.info("訪客模式：僅能投票")

# --- 介面切換 ---

if is_admin:
    # === 管理員模式：顯示三個分頁 ===
    tab1, tab2, tab3 = st.tabs(["1. 主辦人建立", "2. 參與者投票(預覽)", "3. 查看結果"])
    
    # Tab 1: 放入您優化過的「建立會議」程式碼
    with tab1:
        st.header("步驟一：設定會議名稱")
        title = st.text_input("會議名稱", placeholder="例如：Q1 產品規劃會議", value=st.session_state.event_data['title'])
        st.divider()
        st.header("步驟二：新增候選時段")
        col1, col2 = st.columns(2)
        with col1:
            pick_date = st.date_input("選擇日期", min_value=datetime.today(), on_change=reset_time_selection)
        with col2:
            pick_times = st.multiselect("選擇該日期的時段", ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"], key="pick_times")
        
        if st.button("➕ 加入候選清單"):
            if pick_times:
                for t in pick_times:
                    slot_str = f"{pick_date} {t}"
                    if slot_str not in st.session_state.temp_slots:
                        st.session_state.temp_slots.append(slot_str)
                        st.session_state.temp_slots.sort()
                st.toast(f"已加入 {pick_date} 的 {len(pick_times)} 個時段！")
            else:
                st.error("請至少選擇一個時間點。")
        
        st.write("---")
        st.subheader("📋 已選時段預覽")
        if st.session_state.temp_slots:
            grouped_slots = {}
            for slot in st.session_state.temp_slots:
                date_part, time_part = slot.split(' ', 1)
                if date_part not in grouped_slots:
                    grouped_slots[date_part] = []
                grouped_slots[date_part].append(time_part)
            with st.container(border=True):
                for date_key, times in grouped_slots.items():
                    st.markdown(f"<div class='date-header'>📅 {date_key}</div>", unsafe_allow_html=True)
                    badges_html = ""
                    for t in times:
                        badges_html += f"<span class='time-badge'>{t}</span>"
                    st.markdown(badges_html, unsafe_allow_html=True)
                    st.write("")
            col_act1, col_act2 = st.columns([4, 1])
            with col_act2:
                if st.button("🗑️ 全部清空"):
                    st.session_state.temp_slots = []
                    st.rerun()
        else:
            st.info("尚無資料，請由上方加入時段。")
        
        st.divider()
        if st.button("🚀 確認發布會議", type="primary", use_container_width=True):
            if title and st.session_state.temp_slots:
                st.session_state.event_data['title'] = title
                st.session_state.event_data['slots'] = st.session_state.temp_slots.copy()
                st.session_state.event_data['votes'] = {}
                st.balloons()
                st.success(f"會議「{title}」已建立！請切換分頁測試。")
            else:
                st.error("請輸入會議名稱並加入至少一個時段。")

    # Tab 2: 呼叫投票頁面函數
    with tab2:
        show_voting_page()

    # Tab 3: 呼叫結果頁面函數
    with tab3:
        show_results_page()

else:
    # === 訪客模式：只顯示投票頁面 ===
    show_voting_page()
