import requests
import streamlit as st
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# 导入提示词工具
from prompts import load_school_info, get_system_prompt

# ====================== 全局配置 ======================
# 硅基流动API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tabchgnzwvpktqodizygjwciucpufprpiycsivtcmzhjqssf"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
# 相似度阈值（低于该值判定无匹配，跳过大模型）
SIM_THRESHOLD = 0.02
# 别名词典（测试用例10：ZUA映射郑州航院）
ALIAS_DICT = {
    "ZUA": "郑州航空工业管理学院（郑州航院）",
    "郑航": "郑州航空工业管理学院"
}
# ======================================================

# 会话状态初始化
if "user_q" not in st.session_state:
    st.session_state.user_q = ""

# 页面标题
st.title("小航 · 郑州航院校园信息助手")
# 身份下拉选择
user_role = st.selectbox("你的身份：", ["新生", "在校生", "教师"])

# 快捷提问按钮池（分身份）
question_pool = {
    "新生": ["报到流程是什么？","学费怎么缴纳？","宿舍规格几人间？","冒充辅导员转账怎么防？"],
    "在校生": ["在读证明怎么开？","校园卡丢失补办流程？","转专业申请渠道？","图书馆开放时间？"],
    "教师": ["差旅报销流程？","调课申请怎么提交？","教室设备故障报修？","科研项目申报入口？"]
}
st.markdown("### 快捷提问（点击自动填充输入框）")
cols = st.columns(4)
current_qs = question_pool[user_role]
# 渲染快捷按钮
for idx, q in enumerate(current_qs):
    with cols[idx % 4]:
        if st.button(q, key=f"btn_{idx}_{user_role}"):
            st.session_state.user_q = q
            st.rerun()

# 输入框逻辑
user_input = st.text_input("输入你的问题：", value=st.session_state.user_q)
# 按钮回填输入框
if st.session_state.user_q and st.session_state.user_q.strip() != "":
    user_input = st.session_state.user_q
    st.session_state.user_q = ""

# 加载知识库
kb_data = load_school_info()
md_file_list = list(Path("data").glob("*.md"))

# 处理别名替换（解决测试用例10 ZUA识别）
def replace_alias(text: str) -> str:
    for alias, real_name in ALIAS_DICT.items():
        text = text.replace(alias, real_name)
    return text
process_input = replace_alias(user_input.strip())

# 主业务逻辑
if not md_file_list:
    # 测试用例8：data文件夹md文件缺失
    st.warning("⚠️ data目录知识库md文件缺失，请补齐4个文档")
else:
    if process_input:
        # 分片知识库匹配，提升相似度精度
        kb_segments = kb_data.split("\n\n")
        max_sim = 0.0
        vectorizer = TfidfVectorizer()
        for seg in kb_segments:
            if seg.strip() == "":
                continue
            corpus = [seg, process_input]
            tfidf = vectorizer.fit_transform(corpus)
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            if sim > max_sim:
                max_sim = sim

        # 分支1：相似度不足，不调用大模型，直接输出兜底（测试用例11防幻觉）
        if max_sim < SIM_THRESHOLD:
            st.subheader("🤖小航回答：")
            st.write("未收录请拨打0371-66391-6值班室确认相关信息。【来源：新生入学指南.md】")
        # 分支2：匹配到内容，正常请求AI接口
        else:
            request_body = {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [
                    {"role":"system","content":get_system_prompt(user_role, kb_data)},
                    {"role":"user","content":process_input}
                ]
            }
            try:
                # 测试用例5：API超时场景
                res = requests.post(API_URL, headers=HEADERS, json=request_body, timeout=1)
                # 异常分支覆盖
                if res.status_code == 401:
                    st.error("❌ API Key鉴权失败，请重新填写硅基流动密钥，联系老师处理")
                elif res.status_code >= 500:
                    st.error("❌ AI服务器故障，请稍后重试")
                elif res.status_code == 403:
                    st.error("❌ 当前账号无接口调用权限")
                elif res.status_code == 404:
                    st.error("❌ API接口地址错误，请核对链接")
                elif res.status_code != 200:
                    st.error(f"❌ 接口异常，状态码：{res.status_code}")
                else:
                    json_data = res.json()
                    if "choices" not in json_data or len(json_data["choices"]) == 0:
                        st.error("❌ AI未生成有效回答，请更换问题重试")
                    else:
                        ans = json_data["choices"][0]["message"]["content"]
                        st.subheader("🤖小航回答：")
                        st.write(ans)
            except requests.exceptions.Timeout:
                # 测试用例5：超时提示
                st.error("❌ 请求超时，网络延迟过高，请稍后再试")
            except requests.exceptions.ConnectionError:
                # 测试用例6：断网提示
                st.error("❌ 网络连接失败，无法访问AI接口")
            except requests.exceptions.JSONDecodeError:
                st.error("❌ 接口返回文本解析失败")
            except KeyError:
                st.error("❌ 读取AI回答字段出错，接口结构变更")
            except Exception as err:
                st.error(f"❌ 未知运行错误：{str(err)}")
    else:
        # 测试用例4：空输入提示
        st.info("💡 请输入你的问题或点击上方快捷提问按钮")

# 测试用例9：静态离线电话黄页（永久展示无需联网）
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