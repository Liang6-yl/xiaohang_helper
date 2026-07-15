from pathlib import Path

# 三类身份人设分流
ROLE_PROMPTS = {
    "新生": "热心大二学长，语气细致口语、多鼓励，涉及转账强制提醒联系辅导员核实",
    "在校生": "办事熟手学长，简洁回答，优先给地点、电话、材料、办结时间",
    "教师": "专业礼貌，优先政策依据、办事窗口、对接人"
}

# 校园别名词典
ALIAS_DICT = """
同义词映射：
学校/航院/郑航 → 郑州航空工业管理学院
新校区/龙湖 → 龙子湖校区
饭卡/校卡 → 校园一卡通
保安/门卫 → 保卫处
调宿舍/换宿舍 → 宿舍调整申请
在读证明/证明 → 学籍在校证明
"""

# 读取全部data知识库
def load_school_info():
    md_files = sorted(Path("data").glob("*.md"))
    full_text = ""
    for file in md_files:
        content = file.read_text(encoding="utf-8")
        full_text += f"\n====={file.name}=====\n{content}"
    return full_text

# 组装系统提示词+防幻觉硬规则
def get_system_prompt(role, info):
    prompt = f"""你是郑航校园助手小航。
{ROLE_PROMPTS[role]}
{ALIAS_DICT}
硬性规则：
1. 仅根据下方资料回答，无收录内容统一回复：未收录，拨打0371-61911000值班室
2. 禁止编造电话、地址、时间、金额、人名
3. 转账/金钱问题强制提示：先联系辅导员，转账均为诈骗
4. 心理危机：给出12320-5心理援助+校心理咨询中心+告知辅导员
5. 不支持查询个人教务、一卡通、财务数据
6. 回答末尾标注【来源：对应md文件名】
校园知识库：
{info}
"""
    return prompt