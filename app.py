import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# --- 設定頁面 ---
st.set_page_config(page_title="會議時間統整大師", layout="centered")

# --- CSS 美化樣式 ---
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

# --- 載入並編碼圖片 ---
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"

# 這裡需要確保您的圖片 image_0.png 和 app.py 在同一個目錄下
# 如果您的圖片是兩張分開的，請分別準備並替換路徑
# 假設您的圖片是單一張包含兩個圖示的，我們需要切割它 (這在Streamlit不方便)，
# 所以這裡我們假設您已經將圖片切分成兩個檔案：green_check.png 和 red_cross.png
# **請您準備兩張圖片：green_check.png 和 red_cross.png，並放在與 app.py 相同的目錄下**

# 如果沒有圖片，請先建立它們 (這裡用程式碼生成一個紅綠方塊代替，您可以替換成真實圖片路徑)
import numpy as np
from PIL import Image
if not pd.io.common.file_exists("green_check.png"):
    img = Image.fromarray(np.full((20, 20, 3), [0, 255, 0], dtype=np.uint8))
    img.save("green_check.png")
if not pd.io.common.file_exists("red_cross.png"):
    img = Image.fromarray(np.full((20, 20, 3), [255, 0, 0], dtype=np.uint8))
    img.save("red_cross.png")

green_check_img = get_image_base64("green_check.png")
red_cross_img = get_image_base64("red_cross.png")


# --- 邏輯函數 ---
def reset_time_selection():
    st.session_state.pick_times = []

# --- 初始化 Session State ---
if 'event_data' not in st.session_state:
    st.session_state.event_data = {'title': '', 'slots': [], 'votes': {}}

if 'temp_slots' not in st.session_state:
    st.session_state.temp_slots = []

st.title("📅 會議時間統整小幫手 (優化版)")

# 分頁
tab1, tab2, tab3 = st.tabs(["1. 主辦人建立", "2. 參與者投票", "3. 查看結果"])

# ==========================================
# === Tab 1: 主辦人建立會議 (維持不變) ===
# ==========================================
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

# ==========================================
# === Tab 2: 參與者投票 (維持不變) ===
# ==========================================
with tab2:
    st.header("填寫有空的時間")
    current_title = st.session_state.event_data['title']
    current_slots = st.session_state.event_data['slots']
    if not current_title:
        st.warning("👈 請先回到第一頁建立會議。")
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
            if submit and voter_name:
                st.session_state.event_data['votes'][voter_name] = selections
                st.success(f"{voter_name}，您的投票已記錄！")

# ==========================================
# === Tab 3: 查看統計結果 (優化版) ===
# ==========================================
with tab3:
    st.header("統計結果")
    votes_dict = st.session_state.event_data['votes']
    slots = st.session_state.event_data['slots']
    
    if not votes_dict:
        st.info("尚無人投票。")
    else:
        df = pd.DataFrame(votes_dict, index=slots).T
        
      # 1. 定義背景顏色的函數 (在這裡修改色碼)
        def highlight_bg(val):
            # 如果是有空 (True)，背景色設為淺綠色 (#e6f4ea)
            # 如果是沒空 (False)，背景色設為淺紅色 (#fce8e6)
            color = '#e6f4ea' if val else '#fce8e6' 
            return f'background-color: {color}'

        # 2. 定義顯示圖片的函數
        def show_images(val):
            if val:
                # 為了美觀，我們加一點置中樣式
                return f'<div style="text-align:center"><img src="{green_check_img}" width="24" /></div>'
            else:
                return f'<div style="text-align:center"><img src="{red_cross_img}" width="24" /></div>'

        st.write("### 投票明細")
        
        # 3. 應用樣式並渲染
        # map() 用來處理背景色，format() 用來處理圖片內容
        st.write(
            df.style
            .map(highlight_bg)  # 應用背景色
            .format(show_images) # 應用圖片
            .to_html(escape=False), # 轉為 HTML
            unsafe_allow_html=True
        )
        
        # 2. 統計每個時段的總得票數
        vote_counts = df.sum(axis=0)
        best_slot = vote_counts.idxmax()
        max_votes = vote_counts.max()
        
        st.divider()
        st.subheader("🏆 最佳時段推薦")
        st.success(f"目前最佳時段是： **{best_slot}**，共有 **{max_votes}** 人有空。")
        





