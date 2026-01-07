import streamlit as st
import pandas as pd
from datetime import datetime

# --- 設定頁面 ---
st.set_page_config(page_title="會議時間統整大師", layout="centered")

# --- 初始化 Session State (資料庫) ---
# 1. 存放最終確認的會議資料
if 'event_data' not in st.session_state:
    st.session_state.event_data = {
        'title': '',
        'slots': [],
        'votes': {} 
    }

# 2. 存放「建立中」的暫存時段 (像購物車一樣)
if 'temp_slots' not in st.session_state:
    st.session_state.temp_slots = []

st.title("📅 會議時間統整小幫手 (多日版)")
st.info("💡 提示：現在可以跨不同日期選擇多個時段囉！")

# 分頁
tab1, tab2, tab3 = st.tabs(["1. 主辦人建立", "2. 參與者投票", "3. 查看結果"])

# ==========================================
# === Tab 1: 主辦人建立會議 (大幅修改) ===
# ==========================================
with tab1:
    st.header("步驟一：設定會議名稱")
    title = st.text_input("會議名稱", placeholder="例如：Q1 產品規劃會議", value=st.session_state.event_data['title'])
    
    st.divider() # 分隔線
    
    st.header("步驟二：新增候選時段")
    
    # 選擇介面
    col1, col2 = st.columns(2)
    with col1:
        # 選擇日期
        pick_date = st.date_input("選擇日期", min_value=datetime.today())
    with col2:
        # 選擇該日期的時段
        pick_times = st.multiselect("選擇該日期的時段", 
                               ["09:00", "10:00", "11:00", "12:00", 
                                "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"])
    
    # 【加入清單按鈕】
    if st.button("➕ 加入候選清單"):
        if pick_times:
            for t in pick_times:
                # 組合格式：2023-10-20 14:00
                slot_str = f"{pick_date} {t}"
                # 避免重複加入
                if slot_str not in st.session_state.temp_slots:
                    st.session_state.temp_slots.append(slot_str)
                    st.session_state.temp_slots.sort() # 排序讓視覺整齊
            st.success(f"已加入 {len(pick_times)} 個時段！")
        else:
            st.error("請至少選擇一個時間點。")

    # 顯示目前已加入的時段
    st.write("---")
    st.subheader("已選時段預覽：")
    
    if st.session_state.temp_slots:
        # 顯示成一個個的小標籤
        st.write(st.session_state.temp_slots)
        
        # 清除重選按鈕
        if st.button("🗑️ 清空重選"):
            st.session_state.temp_slots = []
            st.rerun() # 重新整理頁面
    else:
        st.caption("目前清單是空的，請上方選擇並加入。")

    st.divider()

    # 【最終生成按鈕】
    if st.button("🚀 確認發布會議", type="primary"):
        if title and st.session_state.temp_slots:
            # 將暫存區轉正
            st.session_state.event_data['title'] = title
            st.session_state.event_data['slots'] = st.session_state.temp_slots.copy() # 複製一份
            st.session_state.event_data['votes'] = {} # 重置投票
            
            st.balloons() # 放氣球慶祝
            st.success(f"會議「{title}」已建立！包含 {len(st.session_state.temp_slots)} 個時段。請切換分頁測試。")
        else:
            st.error("請輸入會議名稱，並至少加入一個時段。")

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
            selections = []
            # 這裡會自動列出所有不同日期的時段
            for slot in current_slots:
                is_selected = st.checkbox(slot, key=slot)
                selections.append(is_selected)
            
            submit = st.form_submit_button("送出投票")
            
            if submit and voter_name:
                st.session_state.event_data['votes'][voter_name] = selections
                st.success(f"{voter_name}，您的投票已記錄！")

# ==========================================
# === Tab 3: 查看統計結果 (維持不變) ===
# ==========================================
with tab3:
    st.header("統計結果")
    
    votes_dict = st.session_state.event_data['votes']
    slots = st.session_state.event_data['slots']
    
    if not votes_dict:
        st.info("尚無人投票。")
    else:
        df = pd.DataFrame(votes_dict, index=slots).T
        st.table(df.applymap(lambda x: "✅" if x else "❌"))
        
        vote_counts = df.sum(axis=0)
        best_slot = vote_counts.idxmax()
        max_votes = vote_counts.max()
        
        st.success(f"🏆 最佳時段： **{best_slot}** ({max_votes} 票)")
        st.bar_chart(vote_counts)
