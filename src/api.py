import requests
import streamlit as st
from pathlib import Path
from src.prompts import load_school_info, get_system_prompt

# 硅基流动API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tabchgnzwvpktqodizygjwciucpufprpiycsivtcmzhjqssf"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 会话状态存储推荐问题
if "user_q" not in st.session_state:
    st.session_state.user_q = ""

# 页面标题
st.title("小航 · 郑州航院校园信息助手")
# 身份下拉选择
user_role = st.selectbox("你的身份：", ["新生", "在校生", "教师"])

# 12个分身份快捷提问按钮（3身份×4个，满足要求）
question_pool = {
    "新生": ["报到流程是什么？","学费怎么缴纳？","宿舍规格几人间？","冒充辅导员转账怎么防？"],
    "在校生": ["在读证明怎么开？","校园卡丢失补办流程？","转专业申请渠道？","图书馆开放时间？"],
    "教师": ["差旅报销流程？","调课申请怎么提交？","教室设备故障报修？","科研项目申报入口？"]
}
st.markdown("### 快捷提问（点击自动填充输入框）")
cols = st.columns(4)
current_qs = question_pool[user_role]
for idx, q in enumerate(current_qs):
    with cols[idx % 4]:
        if st.button(q, key=f"btn_{idx}"):
            st.session_state.user_q = q
            st.rerun()

# 问题输入框
user_input = st.text_input("输入你的问题：", value=st.session_state.user_q)