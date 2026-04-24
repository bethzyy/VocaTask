"""Image description service using GLM-4V-Flash."""
import base64
import logging
from pathlib import Path

from zhipuai import ZhipuAI

import config

logger = logging.getLogger(__name__)

VISION_SYSTEM_PROMPT = """你是事件现场图片速报助手。用一句话说清楚照片里发生了什么。
要求：
- 只说核心：什么对象、什么状态、什么问题
- 不要描写环境氛围、光线、构图等无关内容
- 有文字就直接提取，有损坏就说明损坏部位
- 最多80字，像工作汇报一样精炼
示例：「3号配电柜门变形，内部线缆裸露，地面有水渍」"""


class VisionService:
    """Describes images using GLM-4V-Flash multimodal model."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.ZHIPU_API_KEY
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not configured")
        self.client = ZhipuAI(api_key=self.api_key)

    def describe(self, image_path: str) -> dict:
        """Describe a single image.

        Returns: {"success": bool, "description": str, "error": str | None}
        """
        path = Path(image_path)
        if not path.exists():
            return {"success": False, "description": "", "error": f"File not found: {image_path}"}

        try:
            with open(path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")

            response = self.client.chat.completions.create(
                model=config.VISION_MODEL,
                messages=[
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": img_base64},
                            },
                            {
                                "type": "text",
                                "text": "一句话说明照片中的事件情况。",
                            },
                        ],
                    },
                ],
                temperature=0.1,
                max_tokens=150,
            )

            description = response.choices[0].message.content
            if not description or not description.strip():
                return {"success": False, "description": "", "error": "Vision model returned empty response"}

            return {"success": True, "description": description.strip(), "error": None}

        except Exception as e:
            logger.error("Vision API call failed for %s: %s", image_path, e)
            return {"success": False, "description": "", "error": str(e)}
