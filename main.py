#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv
from stagehand import Stagehand

load_dotenv()  # 自动读取当前目录 .env

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat").strip()
CHROME_PATH = os.getenv("CHROME_PATH", "").strip()

if not DEEPSEEK_API_KEY:
    print("缺少环境变量 DEEPSEEK_API_KEY")
    sys.exit(1)


def build_stagehand():
    return Stagehand(
        server="local",
        browserbase_api_key="local",
        browserbase_project_id="local",
        model_api_key=DEEPSEEK_API_KEY,
        local_headless=False,
        local_port=0,
        local_ready_timeout_s=15.0,
    )


def print_help():
    print("""
可用命令：
  /help                  显示帮助
  /goto <url>            打开网址
  /extract <需求>        提取页面信息
  /quit                  退出

其他自然语言：
  直接交给 Stagehand 执行，例如：
  点击登录按钮
  在搜索框输入 OpenAI 并回车
  返回上一页
""")


def main():
    print("启动 Stagehand LOCAL + DeepSeek ...")
    client = build_stagehand()

    launch_options = {}
    if CHROME_PATH:
        launch_options["executablePath"] = CHROME_PATH

    session = client.sessions.start(
        model_name=DEEPSEEK_MODEL,
        browser={
            "type": "local",
            "launchOptions": launch_options,
        },
    )

    session_id = session.data.session_id
    print(f"浏览器会话已启动: {session_id}")
    print_help()

    try:
        while True:
            try:
                user_input = input("\n你> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n退出。")
                break

            if not user_input:
                continue

            if user_input == "/quit":
                break

            if user_input == "/help":
                print_help()
                continue

            if user_input.startswith("/goto "):
                url = user_input[len("/goto "):].strip()
                if url.startswith("www."):
                    url = "https://" + url
                client.sessions.navigate(id=session_id, url=url)
                print(f"已打开: {url}")
                continue

            if user_input.startswith("/extract "):
                instruction = user_input[len("/extract "):].strip()
                result = client.sessions.extract(
                    id=session_id,
                    instruction=instruction,
                    schema={
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "key_points": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["summary"]
                    },
                )
                print("提取结果：")
                print(result.data.result)
                continue

            result = client.sessions.act(
                id=session_id,
                input=user_input,
            )
            print("执行结果：")
            print(result.data.result)

    finally:
        try:
            client.sessions.end(id=session_id)
        except Exception:
            pass
        client.close()


if __name__ == "__main__":
    main()