# -*- coding: utf-8 -*-
"""
fruit-recognizer 核心识别模块（纯逻辑，无 UI）

输入：OpenCV BGR 图像帧（numpy ndarray）
输出：识别结果 dict，字段：
    is_fruit: bool   是否为水果
    name:    str     水果中文名 / "不是水果"
    emoji:   str     对应 emoji
    desc:    str     一句趣味说明

用法：
    from core.recognizer import recognize_frame
    result = recognize_frame(frame_bgr, api_key="你的智谱API Key")
    print(result["name"], result["emoji"])

设计说明：
    本模块调用智谱 GLM-4V 视觉大模型完成识别，
    不训练本地分类模型，因此可覆盖任意常见水果（含任意角度、任意品种）。
"""
import re
import json
import base64

import cv2
import requests

DEFAULT_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4v-flash"

_PROMPT = (
    "你是水果识别助手。分析这张图片里的主体。只输出一行 JSON，"
    "不要 markdown、不要解释："
    "{\"is_fruit\": true 或 false, "
    "\"name\": \"水果中文名，或主体不是水果时写'不是水果'\", "
    "\"emoji\": \"对应单个水果的 emoji\", "
    "\"desc\": \"一句趣味说明，20 字以内\"}。"
    "如果主体不是水果或画面看不清，is_fruit=false。"
)


def _frame_to_data_url(frame_bgr, quality=80):
    """把 BGR 帧编码为 JPEG base64 data URL"""
    ok, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("图像编码失败")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return "data:image/jpeg;base64," + b64


def _parse_content(content):
    """从模型返回文本中提取 JSON 结果，失败时降级"""
    content = (content or "").strip()
    m = re.search(r"\{.*\}", content, re.S)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                data.setdefault("is_fruit", "不是水果" not in content)
                data.setdefault("name", content[:20] or "未知")
                data.setdefault("emoji", "🍎")
                data.setdefault("desc", "")
                return data
        except Exception:
            pass
    return {
        "is_fruit": "不是水果" not in content,
        "name": content[:20] or "未知",
        "emoji": "🍎" if "不是水果" not in content else "⚠️",
        "desc": "",
    }


def recognize_frame(frame_bgr, api_key, api_url=DEFAULT_API_URL, model=DEFAULT_MODEL,
                    timeout=40):
    """识别一帧图像，返回结果 dict。失败时抛异常。"""
    if frame_bgr is None:
        raise ValueError("图像帧为空")
    if not api_key:
        raise ValueError("缺少智谱 API Key")

    data_url = _frame_to_data_url(frame_bgr)
    body = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": _PROMPT},
            ],
        }],
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.post(api_url, headers=headers, json=body, timeout=timeout)
    data = resp.json()
    if resp.status_code != 200:
        msg = data.get("error", {}).get("message", f"HTTP {resp.status_code}")
        raise RuntimeError(f"识别失败：{msg}")
    content = (data.get("choices", [{}])[0].get("message", {})
               .get("content", "") or "")
    return _parse_content(content)


if __name__ == "__main__":
    # 简单自测：生成一张红色圆形测试图
    import numpy as np
    img = np.full((320, 320, 3), 245, dtype=np.uint8)
    yy, xx = np.mgrid[0:320, 0:320]
    mask = (xx - 160) ** 2 + (yy - 175) ** 2 <= 110 ** 2
    img[mask] = [60, 60, 220]
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    print(recognize_frame(img, key))
