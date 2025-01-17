# users/services/judge_qwen.py
import json
from http import HTTPStatus
import dashscope
import time
import re

SLEEP_TIME = 0.5  # 休眠时间，单位：秒
# 定义正则表达式模式以匹配中文引号
chinese_quotes_pattern = {"single": re.compile(r"[‘’]"), "double": re.compile(r"[“”]")}


def get_judge_from_qwen(
    answer_content: str, PROMPT: str, API_KEY: str, MODEL: str
) -> dict:

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": PROMPT + "\n#### 考生的答案\n" + answer_content,
                },
            ],
        }
    ]
    response = dashscope.Generation.call(
        api_key=API_KEY, model=MODEL, messages=messages, result_format="message"
    )
    time.sleep(SLEEP_TIME)
    # print(response)
    if response.output is None:
        print("未收到响应")
        return {"score": None, "reason": "AI评分失败：未收到响应。"}
    response_text_origin = response.output.choices[0].message.content
    # 替换中文引号为英文引号
    response_text = chinese_quotes_pattern["single"].sub("'", response_text_origin)
    response_text = chinese_quotes_pattern["double"].sub('"', response_text)
    # 去除多余的换行和缩进
    response_text = re.sub(r"\s+", " ", response_text).strip()
    print(response_text)
    if response.status_code == HTTPStatus.OK:
        try:
            response_data = json.loads(response_text)
            # 如果有除了score和reason之外的字段，将它们都归入reason
            for key in response_data.keys():
                if key not in ["score", "reason"]:
                    response_data["reason"] = (
                        response_data.get("reason", "") + f"{response_data.get(key)}\n"
                    )
            print(response_data)
        except json.JSONDecodeError:
            print("JSON解析错误")
            return {"score": None, "reason": "AI评分失败：JSON解析错误。"}
        if isinstance(response_data, dict):
            score = response_data.get("score", None)
            reason = response_data.get("reason", "AI评分失败：未提供评分原因。")
            print(score, reason)
            return {"score": score, "reason": reason}
        else:
            print("格式错误")
            return {"score": None, "reason": "AI评分失败：格式错误。"}
    else:
        print(f"错误码{response.status_code}")
        return {"score": None, "reason": f"AI评分失败：错误码{response.status_code}。"}
