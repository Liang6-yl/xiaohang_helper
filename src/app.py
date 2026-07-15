import requests
import streamlit as st
from pathlib import Path
from src.prompts import load_school_info, get_system_prompt

# 硅基流动API配置
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "粘贴你的硅基流动API Key"
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
# 加载校园知识库
kb_data = load_school_info()
md_files = list(Path("data").glob("*.md"))

# 判断知识库文件缺失
if not md_files:
    st.warning("⚠️ data目录知识库md文件缺失，请补齐4个文档")
else:
    if user_input and user_input.strip():
        request_body = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [
                {"role":"system","content":get_system_prompt(user_role, kb_data)},
                {"role":"user","content":user_input}
            ]
        }
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
                st.error("❌ 当前账号无接口调用权限")
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
    elif user_input is not None:
        st.info("💡 请输入问题或点击上方快捷提问按钮")
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