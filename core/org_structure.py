"""Mock organization structure for task routing."""

ORG_STRUCTURE = {
    "departments": [
        {"id": "equip", "name": "设备部门", "head": "张三", "responsibilities": ["设备检查", "设备维修", "设备采购", "设备保养", "故障排查"]},
        {"id": "prod", "name": "生产部门", "head": "李四", "responsibilities": ["生产计划", "质量控制", "产能管理", "产量统计", "工艺改进"]},
        {"id": "safety", "name": "安全部门", "head": "王五", "responsibilities": ["安全检查", "隐患排查", "应急处理", "消防管理", "安全教育"]},
        {"id": "logistics", "name": "后勤部门", "head": "赵六", "responsibilities": ["物资采购", "仓储管理", "运输调度", "办公用品", "维修申报"]},
        {"id": "hr", "name": "人力资源", "head": "钱七", "responsibilities": ["人员调配", "考勤管理", "培训安排", "招聘入职", "薪酬福利"]},
    ],
    "workshops": ["1号车间", "2号车间", "3号车间", "仓库", "办公楼"],
    "people": [
        {"name": "张三", "department": "设备部门", "title": "设备主管", "phone": "138xxxx0001", "nicknames": ["小张", "老张", "张工"]},
        {"name": "李四", "department": "生产部门", "title": "生产经理", "phone": "139xxxx0002", "nicknames": ["小李", "老李", "李经理"]},
        {"name": "王五", "department": "安全部门", "title": "安全主管", "phone": "137xxxx0003", "nicknames": ["小王", "老王", "王工"]},
        {"name": "赵六", "department": "后勤部门", "title": "后勤主管", "phone": "136xxxx0004", "nicknames": ["小赵", "老赵", "赵主管"]},
        {"name": "钱七", "department": "人力资源", "title": "HR经理", "phone": "135xxxx0005", "nicknames": ["小钱", "老钱", "钱经理"]},
        {"name": "孙八", "department": "设备部门", "title": "设备工程师", "phone": "134xxxx0006", "nicknames": ["小孙", "老孙"]},
        {"name": "周九", "department": "生产部门", "title": "车间主任", "phone": "133xxxx0007", "nicknames": ["小周", "老周"]},
        {"name": "吴十", "department": "安全部门", "title": "安全员", "phone": "132xxxx0008", "nicknames": ["小吴", "老吴"]},
        {"name": "郑冬", "department": "后勤部门", "title": "采购专员", "phone": "131xxxx0009", "nicknames": ["小郑", "老郑"]},
        {"name": "陈明", "department": "人力资源", "title": "培训专员", "phone": "130xxxx0010", "nicknames": ["小陈", "老陈"]},
    ],
}

# Keyword → (department, person) for fallback routing
KEYWORD_RULES = [
    (["设备", "机器", "维修", "检修", "故障", "保养", "运转"], "设备部门", "张三"),
    (["生产", "产量", "工艺", "质量", "产品", "加工", "装配"], "生产部门", "李四"),
    (["安全", "隐患", "消防", "危险", "事故", "防护", "应急"], "安全部门", "王五"),
    (["采购", "物资", "材料", "仓库", "运输", "后勤", "办公"], "后勤部门", "赵六"),
    (["人员", "招聘", "培训", "考勤", "薪酬", "入职", "离职"], "人力资源", "钱七"),
]


def get_org_summary() -> str:
    """Return condensed org structure for LLM context, including nicknames."""
    lines = ["组织架构:"]
    for dept in ORG_STRUCTURE["departments"]:
        members_info = []
        for p in ORG_STRUCTURE["people"]:
            if p["department"] == dept["name"]:
                nicks = p.get("nicknames", [])
                entry = p["name"]
                if nicks:
                    entry += f"（别名/称呼：{'、'.join(nicks)}）"
                members_info.append(entry)
        lines.append(
            f"- {dept['name']}（负责人：{dept['head']}）"
            f"职责：{'、'.join(dept['responsibilities'])} "
            f"成员：{'、'.join(members_info)}"
        )
    lines.append(f"车间/区域：{'、'.join(ORG_STRUCTURE['workshops'])}")
    return "\n".join(lines)


def find_person(name: str) -> dict | None:
    """Look up a person by formal name or nickname."""
    for p in ORG_STRUCTURE["people"]:
        if name in p["name"] or name in p.get("nicknames", []):
            return p
    return None


def keyword_route(text: str) -> dict:
    """Simple keyword-based routing fallback."""
    for keywords, dept, person in KEYWORD_RULES:
        if any(kw in text for kw in keywords):
            return {"department": dept, "assignee": person, "priority": "medium", "method": "keyword_fallback"}
    return {"department": "综合管理", "assignee": "值班人员", "priority": "low", "method": "keyword_fallback"}
