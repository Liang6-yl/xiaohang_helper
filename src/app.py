import streamlit as st
from pathlib import Path
from src.prompts import get_system_prompt, load_school_info
# 如果你用硅基流动，注释下面这行，启用硅基的导入
from src.api import call_doubao_api


def show_phone_directory():
    project_root = Path(__file__).resolve().parent.parent
    phone_file = project_root / "data" / "03_电话黄页.md"
    if phone_file.exists():
        content = phone_file.read_text(encoding="utf-8")
        st.markdown(content)
    else:
        st.error("电话黄页文件未找到")


def main():
    st.set_page_config(page_title="小航 - 郑州航院校园信息助手", page_icon="✈️")

    st.title("✈️ 小航 - 郑州航院校园信息助手")

    # 会话状态初始化
    if "identity" not in st.session_state:
        st.session_state.identity = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "school_info" not in st.session_state:
        st.session_state.school_info = load_school_info()
    if "show_phone_dir" not in st.session_state:
        st.session_state.show_phone_dir = False

    # 分身份12个快捷提问（每组4个，共12个）
    PRESET_QUESTIONS = {
        "新生": [
            "报到那天先去哪？",
            "学费什么时候交？",
            "宿舍是4人间还是6人间？",
            "有人冒充辅导员要钱怎么办？"
        ],
        "在校生": [
            "怎么开在读证明？",
            "校园卡丢了怎么补？",
            "转专业怎么转？",
            "图书馆几点关？"
        ],
        "教师": [
            "差旅怎么报销？",
            "调课怎么申请？",
            "教室设备坏了找谁？",
            "科研项目去哪申报？"
        ]
    }

    # 打开电话黄页页面
    if st.session_state.show_phone_dir:
        st.sidebar.button("返回聊天", on_click=lambda: setattr(st.session_state, "show_phone_dir", False))
        show_phone_directory()
        return

    # 初次选择身份页面
    if not st.session_state.identity:
        st.subheader("请选择您的身份")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("新生"):
                st.session_state.identity = "新生"
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("在校生"):
                st.session_state.identity = "在校生"
                st.session_state.messages = []
                st.rerun()
        with col3:
            if st.button("教师"):
                st.session_state.identity = "教师"
                st.session_state.messages = []
                st.rerun()
    # 已选择身份，进入聊天界面
    else:
        with st.sidebar:
            st.subheader(f"当前身份: {st.session_state.identity}")
            if st.button("切换身份"):
                st.session_state.identity = ""
                st.session_state.messages = []
                st.rerun()

            st.divider()
            if st.button("📞 电话黄页", use_container_width=True):
                st.session_state.show_phone_dir = True
                st.rerun()

            st.divider()
            st.subheader("快捷问题")
            # 根据当前身份读取对应4个问题
            current_quick = PRESET_QUESTIONS[st.session_state.identity]
            # 循环渲染快捷按钮，key带上身份避免缓存冲突
            for idx, q in enumerate(current_quick):
                if st.button(q, use_container_width=True, key=f"q_{idx}_{st.session_state.identity}"):
                    st.session_state.messages.append({"role": "user", "content": q})
                    st.rerun()

        # 渲染历史聊天记录
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 底部输入框
        if prompt := st.chat_input("请问有什么可以帮您的？"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 拼接系统提示词+对话历史
            system_prompt = get_system_prompt(st.session_state.identity, st.session_state.school_info)
            messages_for_api = [{"role": "system", "content": system_prompt}] + st.session_state.messages

            # AI回复区域
            with st.chat_message("assistant"):
                with st.spinner("小航正在思考..."):
                    response = call_doubao_api(messages_for_api)
                    st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()