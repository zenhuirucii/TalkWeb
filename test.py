#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from openai import OpenAI
from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()


SYSTEM_PROMPT = """你是浏览器控制助手。
你必须只返回 JSON，不要输出任何额外解释。

允许的动作:
- goto: 打开网页, 需要 {"url": "..."}
- click: 点击元素, 需要 {"selector": "..."}
- type: 输入文本, 需要 {"selector": "...", "text": "..."}
- extract: 提取页面信息, 需要 {"query": "要提取什么"}

返回格式:
{
  "action": "goto|click|type|extract",
  "args": {...}
}
"""


def ask_llm(user_task: str, page_url: str, page_title: str, page_text: str) -> dict:
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""用户指令: {user_task}

当前页面URL: {page_url}
当前页面标题: {page_title}
当前页面文本摘要:
{page_text[:4000]}

请严格返回 JSON。"""
            },
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    return json.loads(content)


def run_browser_agent():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com")

        print("浏览器已启动。输入 quit 退出。")

        while True:
            user_task = input("\n你> ").strip()
            if not user_task:
                continue
            if user_task.lower() in {"quit", "exit"}:
                break

            page_title = page.title()
            page_url = page.url
            page_text = page.locator("body").inner_text()

            plan = ask_llm(user_task, page_url, page_title, page_text)
            print("LLM 计划:", json.dumps(plan, ensure_ascii=False, indent=2))

            action = plan["action"]
            args = plan["args"]

            if action == "goto":
                page.goto(args["url"])
                print("已打开:", page.url)

            elif action == "click":
                page.locator(args["selector"]).first.click()
                print("已点击:", args["selector"])

            elif action == "type":
                page.locator(args["selector"]).first.fill(args["text"])
                print("已输入:", args["selector"], args["text"])

            elif action == "extract":
                result = page.locator("body").inner_text()
                print("\n提取结果:\n")
                print(result[:3000])

            else:
                print("未知动作:", action)

        browser.close()


if __name__ == "__main__":
    run_browser_agent()