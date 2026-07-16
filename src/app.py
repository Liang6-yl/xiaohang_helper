import requests
import streamlit as st
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

# 会话状态初始化：新增history存储提问历史
if "user_q" not in st.session_state:
    st.session_state.user_q = ""
# 初始化历史记录列表
if "question_history" not in st.session_state:
    st.session_state.question_history = []

# 页面标题
st.title("小航 · 郑州航院校园信息助手")

# 身份下拉选择
user_role = st.selectbox("你的身份：", ["新生", "在校生", "教师"])

# 12个分身份快捷提问（3类身份各4个，满足任务要求）
question_pool = {
    "新生": ["报到流程是什么？","学费怎么缴纳？","宿舍规格几人间？","冒充辅导员转账怎么防？"],
    "在校生": ["在读证明怎么开？","校园卡丢失补办流程？","转专业申请渠道？","图书馆开放时间？"],
    "教师": ["差旅报销流程？","调课申请怎么提交？","教室设备故障报修？","科研项目申报入口？"]
}
st.markdown("### 快捷提问（点击自动填充并查询AI）")
cols = st.columns(4)
current_qs = question_pool[user_role]
# 修复按钮缓存：key增加身份标识，切换身份自动刷新按钮
for idx, q in enumerate(current_qs):
    with cols[idx % 4]:
        if st.button(q, key=f"btn_{idx}_{user_role}"):
            st.session_state.user_q = q
            st.rerun()

# 问题输入框
user_input = st.text_input("输入你的问题：", value=st.session_state.user_q)

# 新增逻辑：点击快捷按钮后自动发起AI请求
if st.session_state.user_q and st.session_state.user_q.strip() != "":
    user_input = st.session_state.user_q
    st.session_state.user_q = ""

# ============ 历史记录 移到输入框下方 ============
st.divider()
st.subheader("📜 提问历史")
if len(st.session_state.question_history) == 0:
    st.info("暂无提问记录，输入问题开始查询吧")
else:
    # 倒序展示，最新提问在最上方
    for idx, old_q in enumerate(reversed(st.session_state.question_history)):
        if st.button(f"{old_q}", key=f"history_{idx}"):
            st.session_state.user_q = old_q
            st.rerun()
# 清空历史按钮
if st.button("清空全部历史记录"):
    st.session_state.question_history = []
    st.rerun()
st.divider()
# ==============================================

# 别名替换预处理（解决ZUA识别测试用例）
def replace_alias(text):
    for k, v in INPUT_ALIAS.items():
        text = text.replace(k, v)
    return text
process_text = replace_alias(user_input.strip())

# 加载校园知识库
kb_data = load_school_info()
md_files = list(Path("data").glob("*.md"))

# 判断知识库文件缺失
if not md_files:
    st.warning("⚠️ data目录知识库md文件缺失，请补齐4个文档")
else:
    if process_text:
        # 把当前问题存入历史记录（去重，不重复保存相同问题）
        if process_text not in st.session_state.question_history:
            st.session_state.question_history.append(process_text)

        request_body = {
            "model": "zai-org/GLM-5.2",
            "max_tokens": 1024,    # 新增：提升最大输出长度，防止回答截断不全
            "temperature": 0.01,    # 新增：降低随机性，减少错别字、随意改写
            "messages": [
                {"role":"system","content":get_system_prompt(user_role, kb_data)},
                {"role":"user","content":process_text}
            ]
        }
        # 转圈加载动画
        with st.spinner("🤖 小航正在思考中..."):
            try:
                res = requests.post(API_URL, headers=HEADERS, json=request_body, timeout=30)
                # 异常1：API密钥失效401
                if res.status_code == 401:
                    st.error("❌ API Key鉴权失败，请重新填写硅基流动密钥")
                # 异常2：服务器内部错误5xx
                elif res.status_code >= 500:
                    st.error("❌ AI服务器故障，请稍后重试")
                # 异常3：无访问权限403
                elif res.status_code == 403:
                    st.error("❌ 当前账号无接口访问权限")
                # 异常4：接口地址不存在404
                elif res.status_code == 404:
                    st.error("❌ API接口地址错误，请核对链接")
                # 异常5：其他HTTP错误码
                elif res.status_code != 200:
                    st.error(f"❌ 接口异常，状态码：{res.status_code}")
                else:
                    json_data = res.json()
                    # 异常6：返回无choices字段
                    if "choices" not in json_data:
                        st.error("❌ AI返回数据格式错误，缺少回答内容")
                    # 异常7：回答数组为空
                    elif len(json_data["choices"]) == 0:
                        st.error("❌ AI未生成回答，请更换问题重试")
                    # 正常输出AI回复
                    else:
                        ans = json_data["choices"][0]["message"]["content"]
                        st.subheader("🤖小航回答：")
                        st.write(ans)
            # 异常8：请求超时
            except requests.exceptions.Timeout:
                st.error("❌ 请求超时，网络延迟过高，请重新提问")
            # 异常9：网络断连
            except requests.exceptions.ConnectionError:
                st.error("❌ 网络连接失败，无法访问AI接口")
            # 异常10：返回非JSON格式
            except requests.exceptions.JSONDecodeError:
                st.error("❌ 接口返回文本解析失败")
            # 异常11：字段读取键错误
            except KeyError:
                st.error("❌ 读取AI回答字段出错，接口结构变更")
            # 异常12：兜底全部未知错误
            except Exception as err:
                st.error(f"❌ 未知运行错误：{str(err)}")
    elif process_text == "":
        st.info("💡 请输入你的问题或点击上方快捷提问按钮")

# 离线静态电话黄页（断网/API失效独立展示）
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