import requests
import streamlit as st
# 页面宽屏配置，放在所有代码最顶部
st.set_page_config(page_title="小航 · 郑州航院校园信息助手", layout="wide")
# 去除页面四周空白
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

import time
from pathlib import Path

# 硅基流动API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tabchgnzwvpktqodizygjwciucpufprpiycsivtcmzhjqssf"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 本地输入替换别名词典
INPUT_ALIAS = {
    "ZUA": "郑州航空工业管理学院",
    "郑航": "郑州航空工业管理学院",
    "航院": "郑州航空工业管理学院"
}

# ========== 会话状态初始化（多轮对话messages） ==========
if "user_q" not in st.session_state:
    st.session_state.user_q = ""
# 全局提问历史
if "question_history" not in st.session_state:
    st.session_state.question_history = []
# 多轮上下文对话存储
if "messages" not in st.session_state:
    st.session_state["messages"] = []
# 新增：身份会话存储，解决切换不生效
if "user_role" not in st.session_state:
    st.session_state.user_role = "新生"

# 内置完整知识库（永久可用，不需要data文件夹md文件）
def load_school_info():
    kb_content = """
# 郑州航空工业管理学院校园知识库
## 图书馆相关信息
1. 龙子湖校区图书馆日常开放时间：自习区域7:00-22:30，周一至周日全天开放；
2. 图书借阅厅开放：
   - 第一借阅厅（文学、经管、外语类）：周一至周日 8:30-16:50
   - 第二、第三借阅厅（理工、思政类）：仅周一至周五 8:30-16:50，周末不开放
3. 数字图书馆电子资源：校园网/VPN环境下24小时全天可用
4. 入馆要求：携带本人校园卡刷卡入馆，自习座位需要提前在郑航图书馆公众号预约
5. 节假日、寒暑假会临时调整开放时段，以图书馆官网通知为准
6. 图书馆共7层，阅览座位近5500席，提供空调、热水、研讨间等配套

## 新生相关
1. 报到流程：线上完成迎新系统信息填报、学费住宿费预缴，报到当天携带身份证、录取通知书、档案、一寸照片到对应院系报到处核验，领取校园卡、宿舍钥匙、军训物资；
2. 学费缴纳：迎新系统线上缴费、银行卡代扣、现场财务处窗口缴费三种方式；
3. 宿舍规格：4人间上床下桌，独立阳台，公共卫浴，配备空调、书桌衣柜；
4. 军训物资：防晒用品、舒适运动鞋、水杯、床上用品、驱蚊用品，学校统一发放军训服。

## 办事流程
1. 在读证明：携带校园卡到行政楼302教务科自助打印机打印；
2. 校园卡丢失补办：网信中心一楼服务台挂失补办，工本费20元；办理时需携带本人身份证或学生证，先完成线上挂失，再现场制卡，当场可取新卡；
3. 转专业申请：大一下学期4月提交申请，教务处组织考核，择优调剂；
4. 差旅报销：填写报销单，附发票、行程单，院系签字后交财务处；
5. 调课申请：教师在教务系统提交调课申请，院系教务员审核通过生效。

## 应急防骗
1. 冒充辅导员转账：任何要求私下转账、缴费的消息均为诈骗，缴费仅走学校官方迎新/财务系统，先联系辅导员核实；
2. 教室设备故障报修：拨打后勤报修0371-61913110；
3. 科研项目申报入口：学校科研处官网系统；
4. 校外兼职骗局：刷单、先交押金、高薪日结均为骗局，校内勤工助学统一学工处发布。

## 教职工专属
教学调课、科研项目申报、教师办公场地、经费报销、教职工图书馆借阅权限、教务系统操作指南。
"""
    return kb_content

kb_data = load_school_info()
# 不再读取外部md文件，屏蔽外部文件校验
md_files = []

# 页面标题
st.title("小航 · 郑州航院校园信息助手")

# ===================== 左右分栏布局（左3右7 全屏适配） =====================
left_col, right_col = st.columns([3, 7])

# ---------------------- 左侧：全部功能面板 ----------------------
with left_col:
    st.markdown("## 功能面板")
    # 身份选择（移除on_change=st.rerun，消除警告）
    user_role = st.selectbox(
        "你的身份：",
        ["新生", "在校生", "教师"],
        index=["新生", "在校生", "教师"].index(st.session_state.user_role)
    )
    st.session_state.user_role = user_role
    st.info(f"当前咨询身份：{st.session_state.user_role}")

    st.divider()
    # 快捷提问标签页
    st.markdown("### 快捷提问")
    tab1, tab2, tab3 = st.tabs(["新生指南", "办事流程", "应急防骗"])

    with tab1:
        new_qs = ["报到流程是什么？","学费怎么缴纳？","宿舍规格几人间？","军训需要准备什么？"]
        cols = st.columns(2)
        for idx, q in enumerate(new_qs):
            with cols[idx % 2]:
                if st.button(q, key=f"tab_new_{idx}"):
                    st.session_state.user_q = q

    with tab2:
        process_qs = ["在读证明怎么开？","校园卡丢失补办流程？","转专业申请渠道？","图书馆开放时间？","差旅报销流程？","调课申请怎么提交？"]
        cols = st.columns(2)
        for idx, q in enumerate(process_qs):
            with cols[idx % 2]:
                if st.button(q, key=f"tab_proc_{idx}"):
                    st.session_state.user_q = q

    with tab3:
        safe_qs = ["冒充辅导员转账怎么防？","教室设备故障报修？","科研项目申报入口？","校外兼职骗局如何识别？"]
        cols = st.columns(2)
        for idx, q in enumerate(safe_qs):
            with cols[idx % 2]:
                if st.button(q, key=f"tab_safe_{idx}"):
                    st.session_state.user_q = q

    st.divider()
    # 问题输入框
    user_input = st.text_input("输入你的问题：", value=st.session_state.user_q)

    # 回填逻辑
    if st.session_state.user_q and st.session_state.user_q.strip() != "":
        user_input = st.session_state.user_q
        st.session_state.user_q = ""

    # 操作按钮
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🆕 新对话"):
            st.session_state["messages"] = []
    with col_btn2:
        export_text = ""
        if st.session_state["messages"]:
            export_text += "===== 郑州航院小航对话记录 =====\n\n"
            for msg in st.session_state["messages"]:
                if msg["role"] == "user":
                    export_text += f"【用户提问】{msg['content']}\n"
                elif msg["role"] == "assistant":
                    export_text += f"【AI回答】{msg['content']}\n"
                    export_text += "----------------------------------------\n\n"
        file_name = f"小航对话记录_{time.strftime('%Y%m%d')}.txt"
        st.download_button("📥 导出记录", data=export_text, file_name=file_name, mime="text/plain")

    st.divider()
    # 提问历史
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.subheader("📜 提问历史")
    with col_h2:
        if st.button("清空历史"):
            st.session_state.question_history = []

    if len(st.session_state.question_history) == 0:
        st.info("暂无提问记录")
    else:
        for idx, old_q in enumerate(reversed(st.session_state.question_history)):
            if st.button(f"{old_q}", key=f"history_{idx}"):
                st.session_state.user_q = old_q

    st.divider()
    # 校园电话黄页（新增图书馆电话）
    st.header("📞 校园电话黄页")
    yellow_page_text = """
| 部门 | 24h/办公电话 |
|------|------|
| 校园保卫处110 | 0371-61916110 |
| 学校总值班室 | 0371-61911000 |
| 后勤物业报修 | 0371-61913110 |
| 校医院急诊 | 0371-61912730 |
| 招生办公室 | 0371-61916161 |
| 网信中心 | 0371-61912718 |
| 图书馆服务台 | 0371-61916810 |
    """
    st.markdown(yellow_page_text)

# ---------------------- 右侧：AI回答展示区域（已删除底部历史对话上下文模块） ----------------------
with right_col:
    st.markdown("## AI对话回答区")
    process_text = ""
    if user_input:
        # 别名替换预处理
        def replace_alias(text):
            for k, v in INPUT_ALIAS.items():
                text = text.replace(k, v)
            return text
        process_text = replace_alias(user_input.strip())

    # 直接使用内置知识库，不再校验外部md文件
    if process_text == "":
        st.info("💡 在左侧输入问题或点击快捷提问")

    if process_text:
        # 超长文本提醒
        if len(process_text) > 600:
            st.warning("⚠️ 问题文本过长，建议拆分提问")

        # 存入提问历史
        if process_text not in st.session_state.question_history:
            st.session_state.question_history.append(process_text)

        current_role = st.session_state.user_role
        # 身份人设区分
        if current_role == "教师":
            greet = "老师您好"
            role_tips = "面向教职工，语气正式书面，称呼对方为老师，不使用同学、学弟学妹，完整详细讲解教学、科研、经费、教务业务，分点清晰说明全部步骤。"
        elif current_role == "在校生":
            greet = "同学你好"
            role_tips = "面向在校生，回答完整详细，分步骤说明办事材料、地点、流程、注意事项，称呼对方为同学。"
        else:
            greet = "学弟/学妹你好"
            role_tips = "面向新生，语气温柔细致，完整科普所有相关细节，多鼓励，缴费转账类问题强制提醒联系辅导员核实。"

        system_prompt = f"""你是郑州航院专属校园助手「小航」。
【人设规则】
{role_tips}
开场礼貌使用问候语：{greet}。
【硬性强制输出要求】
1. 仅允许使用下方知识库内全部相关信息回答，严禁编造任何电话、时间、流程、地点；
2. 必须完整展开所有相关内容，分点清晰说明，禁止只输出一句话极简回答，尽可能细化流程、材料、时间、地点、注意事项；
3. 知识库无对应内容才回复：目前知识库中暂无相关内容。建议您查阅学校官方发布的《新生入学须知》或联系招生办公室、学生工作部获取最新权威信息；
4. 学费、缴费、转账相关问题结尾必须提醒：缴费前务必先联系辅导员核实，谨防冒充老师转账诈骗；
5. 严格按照当前身份使用对应称呼，禁止混用口吻；
知识库内容：
{kb_data}
"""
        full_messages = [{"role": "system", "content": system_prompt}] + st.session_state["messages"]
        full_messages.append({"role": "user", "content": process_text})

        request_body = {
            "model": "deepseek-ai/DeepSeek-V3.2",
            "max_tokens": 600,
            "temperature": 0.4,  # 关键修改：从0.01上调至0.4，允许适度扩写细节
            "messages": full_messages
        }

        with st.spinner("🤖 小航正在思考中..."):
            max_retry = 2
            retry_count = 0
            success_flag = False
            res = None
            ans = ""
            skip_render = False
            start = time.time()

            while retry_count <= max_retry and not success_flag:
                try:
                    res = requests.post(API_URL, headers=HEADERS, json=request_body, timeout=90)
                    success_flag = True
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count <= max_retry:
                        st.warning(f"请求超时，第{retry_count}次重试...")
                    else:
                        st.error("❌ 多次请求超时，网络延迟过高")
                        skip_render = True
                        break
                except requests.exceptions.ConnectionError:
                    st.error("❌ 网络连接失败，无法访问AI接口")
                    skip_render = True
                    break

            if skip_render:
                pass
            else:
                if res.status_code == 401:
                    st.error("❌ API Key鉴权失败")
                elif res.status_code >= 500:
                    st.error("❌ AI服务器故障，请稍后重试")
                elif res.status_code == 403:
                    st.error("❌ 账号无接口访问权限")
                elif res.status_code == 404:
                    st.error("❌ API接口地址错误")
                elif res.status_code != 200:
                    st.error(f"❌ 接口异常，状态码：{res.status_code}")
                else:
                    try:
                        json_data = res.json()
                    except requests.exceptions.JSONDecodeError:
                        st.error("❌ 接口返回解析失败")
                    else:
                        if "choices" not in json_data or len(json_data["choices"]) == 0:
                            st.error("❌ AI未生成有效回答")
                        else:
                            ans = json_data["choices"][0]["message"].get("content", "").strip()
                            end = time.time()
                            cost_time = end - start
                            if not ans:
                                st.error("❌ AI返回回答为空，请重新提问")
                            else:
                                st.subheader("🤖小航回答：")
                                st.write(ans)
                                st.caption(f"回答字数：{len(ans)} 字 · 耗时：{cost_time:.1f} 秒")
                                # 保存上下文记忆
                                st.session_state["messages"].append({"role": "user", "content": process_text})
                                st.session_state["messages"].append({"role": "assistant", "content": ans})