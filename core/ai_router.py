"""AI-powered task analysis via Anthropic-compatible endpoint."""
import json
import logging
import re

import anthropic

import config
from core.org_structure import get_org_summary

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=config.AI_ROUTER_API_KEY,
            base_url=config.AI_ROUTER_BASE_URL,
        )
    return _client


_SYSTEM = """你是一个工厂任务分派专家。根据用户的语音描述和组织架构，分析任务内容，
将任务分配给最合适的负责人和部门。

分配规则（按优先级）：
1. 【最高优先级】检查输入中是否出现了人名或称呼，不限位置：
   - 句首："小张，去处理"
   - 句尾："买下来，小张" / "交给老王"
   - 句中："让小张去买" / "叫李四来修"
   只要出现了人名，必须优先分配给该人。别名列表：小张=张三，小李=李四，小王=王五，小赵=赵六，以此类推。
2. 若找到了人名但组织架构中无对应人员：
   - assignee 填写职责最相近的人
   - reason 必须说明："输入提到[原称呼]，组织架构中无此人，已改派给[assignee]"
3. 若没有提到任何人名，再根据任务内容和职责匹配最合适的部门负责人。

必须返回合法 JSON，字段如下：
{
  "assignee": "姓名（必须是组织架构中存在的人）",
  "department": "部门名称",
  "priority": "high|medium|low",
  "task_description": "简明任务描述（不超过50字）",
  "reason": "一句话说明分配理由"
}

优先级规则：
- high：紧急/安全/故障停产
- medium：影响效率但不紧急
- low：日常/可延后

只返回 JSON，不要其他内容。"""


def analyze(transcribed_text: str, image_context: str | None = None) -> dict | None:
    """Call AI to analyze a task. Returns parsed dict or None on failure."""
    if not config.AI_ROUTER_API_KEY:
        logger.warning("AI router API key not configured, skipping analysis")
        return None

    org = get_org_summary()
    user_content = f"组织架构：\n{org}\n\n任务描述：{transcribed_text}"
    if image_context:
        user_content += f"\n\n图片信息：{image_context}"

    try:
        resp = _get_client().messages.create(
            model=config.AI_ROUTER_MODEL,
            max_tokens=512,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = resp.content[0].text.strip()
        # Extract JSON even if wrapped in markdown code block
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            logger.warning("AI returned no JSON: %s", raw[:200])
            return None
        result = json.loads(m.group())
        # Validate required fields
        if not result.get("assignee") or not result.get("department"):
            return None
        logger.info("AI analysis: %s → %s / %s / %s",
                    transcribed_text[:40], result.get("assignee"),
                    result.get("department"), result.get("priority"))
        return result
    except Exception as e:
        logger.error("AI analysis failed: %s", e)
        return None
