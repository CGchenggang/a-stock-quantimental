# -*- coding: utf-8 -*-
"""feishu_pusher.py — 飞书推送模块（重建版）
配置文件 database/feishu_config.json:
  {"webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"}
未配置时打印到控制台并降级为 no-op。
"""
import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG = os.path.join(SKILL_ROOT, "database", "feishu_config.json")


def _webhook():
    if os.path.exists(CONFIG):
        try:
            with open(CONFIG, encoding="utf-8") as f:
                return json.load(f).get("webhook", "")
        except Exception:
            return ""
    return os.environ.get("FEISHU_WEBHOOK", "")


def _post(payload):
    hook = _webhook()
    if not hook:
        print("[feishu] 未配置webhook，仅打印: %s" % payload.get("msg_type"))
        return False
    import requests
    try:
        r = requests.post(hook, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print("[feishu] 推送失败: %s" % str(e)[:80])
        return False


def push_text(text):
    return _post({"msg_type": "text", "content": {"text": text}})


def send_md(title, md_text):
    return _post({"msg_type": "interactive", "card": {
        "header": {"title": {"tag": "plain_text", "content": title}},
        "elements": [{"tag": "markdown", "content": md_text[:9000]}],
    }})


if __name__ == "__main__":
    ok = push_text("feishu_pusher 测试 %s" % datetime.now())
    print("推送结果:", ok)
