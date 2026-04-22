"""Task routing using GLM-4-flash function calling."""
import json
import logging

from zhipuai import ZhipuAI

import config
from core.org_structure import get_org_summary, keyword_route

logger = logging.getLogger(__name__)

ROUTE_TASK_TOOL = {
    "type": "function",
    "function": {
        "name": "route_task",
        "description": "将任务分配给合适的部门和人员",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "简明的任务描述"},
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "优先级：high=紧急/安全相关, medium=常规, low=不急",
                },
                "department": {"type": "string", "description": "负责部门名称"},
                "assignee": {"type": "string", "description": "负责人姓名"},
                "reason": {"type": "string", "description": "分配理由（一句话）"},
                "deadline_suggestion": {"type": "string", "description": "建议完成时间"},
            },
            "required": ["task_description", "priority", "department", "assignee"],
        },
    },
}

SYSTEM_PROMPT = """你是一个任务路由助手。根据用户的语音输入，理解任务意图，并分配给最合适的部门和人员。

规则：
1. 优先分配给被明确提到的人员
2. 如果没有提到具体人员，根据任务内容匹配最合适的部门负责人
3. 安全相关的任务优先级为 high
4. 日常任务为 medium，不紧急的为 low
5. 用中文回复"""


class TaskRouter:
    """Routes tasks to people/departments using GLM-4-flash."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ZHIPU_API_KEY
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not configured")
        self.client = ZhipuAI(api_key=self.api_key)

    def route(self, text: str) -> dict:
        """Route a task. Returns {success, routing: {task_description, priority, department, assignee, reason}}."""
        if not text or not text.strip():
            return {"success": False, "routing": {}, "error": "Empty text, nothing to route"}

        try:
            response = self.client.chat.completions.create(
                model=config.ROUTING_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + get_org_summary()},
                    {"role": "user", "content": text},
                ],
                tools=[ROUTE_TASK_TOOL],
                tool_choice={"type": "function", "function": {"name": "route_task"}},
                temperature=0.1,
                max_tokens=500,
            )

            msg = response.choices[0].message
            if not msg.tool_calls:
                return {"success": False, "routing": {}, "error": "LLM did not return a routing decision"}

            args_str = msg.tool_calls[0].function.arguments
            routing = json.loads(args_str) if isinstance(args_str, str) else args_str
            routing["method"] = "glm_function_calling"

            return {"success": True, "routing": routing, "error": None}

        except json.JSONDecodeError as e:
            logger.error("Failed to parse routing JSON: %s", e)
            fallback = keyword_route(text)
            return {"success": True, "routing": fallback, "error": "JSON parse error, used keyword fallback"}

        except Exception as e:
            logger.error("Routing API call failed: %s", e)
            fallback = keyword_route(text)
            return {
                "success": True,
                "routing": fallback,
                "error": f"API error ({type(e).__name__}), used keyword fallback",
            }
