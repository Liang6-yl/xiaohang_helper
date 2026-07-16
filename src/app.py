import requests
import streamlit as st
import time  # 新增：用于API耗时统计
from pathlib import Path
# 修复模块导入报错：移除src.，使用同目录相对导入
from prompts import load_school_info, get_system_prompt

# 硅基流动API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tabchgnzwvpktqodizygjwciucpufprpiycsivtcmzhjqssf"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 本地输入替换别名词典（和prompt内规则同步）
INPUT_ALIAS = {
    "ZUA": "郑州航空工业管理学院",
    "郑航": "郑州航空工业管理学院",
    "航院": "郑州航空工业管理学院"
}

# 会话状态初始化
if "user_q" not in st.session_state:
    st.session_state.user_q = ""
if "question_history" not in st.session_state:
    st.session_state.question_history = []

# ===================== 优化：知识库仅启动加载一次，不再每次提问重复读取 =====================
kb_data = load_school_info()
md_files = list(Path("data").glob("*.md"))

# 页面标题
st.title("小航 · 郑州航院校园信息助手")

# 身份下拉选择
user_role = st.selectbox("你的身份：", ["新生", "在校生", "教师"])

# 【功能5 4分类标签页：新生指南/办事流程/应急防骗/交通出行】
st.markdown("### 快捷提问（点击自动填充并查询AI）")
tab1, tab2, tab3, tab4 = st.tabs(["新生指南", "办事流程", "应急防骗", "交通出行"])

# 标签1：新生指南
with tab1:
    new_qs = ["报到流程是什么？","学费怎么缴纳？","宿舍规格几人间？","军训需要准备什么？"]
    cols = st.columns(2)
    for idx, q in enumerate(new_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_new_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 标签2：办事流程
with tab2:
    process_qs = ["在读证明怎么开？","校园卡丢失补办流程？","转专业申请渠道？","图书馆开放时间？","差旅报销流程？","调课申请怎么提交？"]
    cols = st.columns(2)
    for idx, q in enumerate(process_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_proc_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 标签3：应急防骗
with tab3:
    safe_qs = ["冒充辅导员转账怎么防？","教室设备故障报修？","科研项目申报入口？","校外兼职骗局如何识别？"]
    cols = st.columns(2)
    for idx, q in enumerate(safe_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_safe_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 标签4：交通出行（6个交通快捷键）
with tab4:
    traffic_qs = [
        "怎么坐地铁去学校？",
        "到郑航可以坐哪几路公交？",
        "郑州东站怎么到龙子湖校区？",
        "新生报到有迎新大巴吗？",
        "自驾入校停车怎么收费？",
        "学校有没有校内通勤校车？"
    ]
    cols = st.columns(2)
    for idx, q in enumerate(traffic_qs):
        with cols[idx % 2]:
            if st.button(q, key=f"tab_traffic_{idx}"):
                st.session_state.user_q = q
                st.rerun()

# 问题输入框
user_input = st.text_input("输入你的问题：", value=st.session_state.user_q)

# 快捷按钮自动填充逻辑
if st.session_state.user_q and st.session_state.user_q.strip() != "":
    user_input = st.session_state.user_q
    st.session_state.user_q = ""

# 别名替换预处理
def replace_alias(text):
    for k, v in INPUT_ALIAS.items():
        text = text.replace(k, v)
    return text
process_text = replace_alias(user_input.strip())

# 判断知识库文件缺失
if not md_files:
    st.warning("⚠️ data目录知识库md文件缺失，请补齐4个文档（包含05_交通出行.md）")
else:
    # 空输入提示
    if process_text == "":
        st.info("💡 请输入你的问题或点击上方快捷提问按钮")

    # 提问历史区域（标题右侧放置清空按钮）
    st.divider()
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("📜 提问历史")
    with col2:
        if st.button("清空全部历史记录"):
            st.session_state.question_history = []
            st.rerun()

    # 历史列表展示
    if len(st.session_state.question_history) == 0:
        st.info("暂无提问记录，输入问题开始查询吧")
    else:
        for idx, old_q in enumerate(reversed(st.session_state.question_history)):
            if st.button(f"{old_q}", key=f"history_{idx}"):
                st.session_state.user_q = old_q
                st.rerun()
    st.divider()

    if process_text:
        # 超长文本友好提示（支持500字，超过600字提醒拆分）
        if len(process_text) > 600:
            st.warning("⚠️ 问题文本过长，建议拆分为2段提问，减少超时概率；当前仍可提交尝试")

        # 历史记录去重保存
        if process_text not in st.session_state.question_history:
            st.session_state.question_history.append(process_text)

        # 请求体优化：DeepSeek-V3.2，适度降低max_tokens减少推理耗时
        request_body = {
            "model": "deepseek-ai/DeepSeek-V3.2",
            "max_tokens": 600,
            "temperature": 0.01,
            "messages": [
                {"role":"system","content":get_system_prompt(user_role, kb_data)},
                {"role":"user","content":process_text}
            ]
        }

        # 加载动画 + 自动重试逻辑
        with st.spinner("🤖 小航正在思考中..."):
            max_retry = 2
            retry_count = 0
            success_flag = False
            res = None
            ans = ""
            skip_render = False

            # 超时重试循环
            while retry_count <= max_retry and not success_flag:
                try:
                    start = time.time()  # 功能6：记录API请求起始时间
                    res = requests.post(API_URL, headers=HEADERS, json=request_body, timeout=90)
                    success_flag = True
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count <= max_retry:
                        st.warning(f"请求超时，正在第{retry_count}次重试...")
                    else:
                        st.error("❌ 多次请求超时，网络延迟过高，请拆分简短问题或切换手机热点重试")
                        skip_render = True
                        break
                except requests.exceptions.ConnectionError:
                    st.error("❌ 网络连接失败，无法访问AI接口")
                    skip_render = True
                    break

            # 重试失败，直接跳过回答渲染
            if skip_render:
                pass
            else:
                # HTTP状态码校验
                if res.status_code == 401:
                    st.error("❌ API Key鉴权失败，请重新填写硅基流动密钥")
                elif res.status_code >= 500:
                    st.error("❌ AI服务器故障，请稍后重试")
                elif res.status_code == 403:
                    st.error("❌ 当前账号无接口访问权限")
                elif res.status_code == 404:
                    st.error("❌ API接口地址错误，请核对链接")
                elif res.status_code != 200:
                    st.error(f"❌ 接口异常，状态码：{res.status_code}")
                else:
                    # JSON解析容错
                    try:
                        json_data = res.json()
                    except requests.exceptions.JSONDecodeError:
                        st.error("❌ 接口返回文本解析失败")
                    else:
                        # 校验返回数据结构
                        if "choices" not in json_data or len(json_data["choices"]) == 0:
                            st.error("❌ AI未生成有效回答，请缩短问题长度重试")
                        else:
                            # 使用get容错，防止message/content键缺失报错空白
                            ans = json_data["choices"][0]["message"].get("content", "").strip()
                            end = time.time()  # 功能6：请求结束计时
                            cost_time = end - start
                            if not ans:
                                st.error("❌ AI返回回答为空，请拆分长提问重新发送")
                            else:
                                # 全部校验通过，展示回答
                                st.subheader("🤖小航回答：")
                                st.write(ans)
                                # 功能6：小字展示字数+耗时元信息
                                st.caption(f"回答字数：{len(ans)} 字 · 耗时：{cost_time:.1f} 秒")

# 离线静态电话黄页（断网兜底）
st.divider()
st.header("📞 校园电话黄页（离线兜底，无需联网）")
st.caption("AI接口故障时，可直接查看官方联系电话")
yellow_page_text = """
| 部门 | 24h/办公电话 |
|------|------|
| 校园保卫处110 | 0371-61916110 |
| 学校总值班室 | 0371-61911000 |
| 后勤物业报修 | 0371-61913110 |
| 校医院急诊 | 0371-61912730 |
| 招生办公室 | 0371-61916161 |
| 网信中心 | 0371-61912718 |
"""
st.markdown(yellow_page_text)