# users/services/judge_gpt.py
import requests
import json
import time

# =======================
# Configuration
# =======================
API_URL = "https://aigptx.top/v1/chat/completions"
# 可选API_URL：
# "https://cn2us02.opapi.win/v1/chat/completions"
# "https://api.ohmygpt.com/v1/chat/completions"
# "https://cn2us02.opapi.win/v1/chat/completions"
# "https://c-z0-api-01.hash070.com/v1/chat/completions"
# "https://aigptx.top/v1/chat/completions"
# "https://cfwus02.opapi.win/v1/chat/completions"
SLEEP_TIME = 0.5  # 休眠时间，单位：秒


def generate_payload(MODEL, user_prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                ],
            },
        ],
        "max_tokens": 300,
    }
    return payload


def get_judge_from_gpt(
    answer_content: str, PROMPT: str, API_KEY: str, MODEL: str
) -> dict:
    HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = generate_payload(MODEL, PROMPT + "\n#### 考生的答案\n" + answer_content)
    # 发送请求
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    time.sleep(SLEEP_TIME)
    print(response)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {"score": None, "reason": "AI评分失败：未收到响应。"}
    if response.status_code == 200:
        result = response.json()
        response_text = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No response generated.")
        )
        response_data = json.loads(response_text)
        if isinstance(response_data, dict):
            score = response_data.get("score", None)
            reason = response_data.get("reason", "AI评分失败：未提供评分原因。")
            return {"score": score, "reason": reason}
        else:
            return {"score": None, "reason": "AI评分失败：格式错误。"}
    else:
        return {"score": None, "reason": "AI评分失败：错误码{response.status_code}。"}
