import os
import sys
from datetime import datetime
import json
import requests

# ==================== 🔧 核心配置区 ====================
LOGIN_URL = "https://laehfeigoiycigkfknfn.supabase.co/auth/v1/token?grant_type=password"
EMAIL = os.getenv("MY_EMAIL")
PASSWORD = os.getenv("MY_PASSWORD")
SUPABASE_ANON_KEY = os.getenv("ANON_KEY")

# Telegram 推送配置
TG_TOKEN = os.getenv("TG_TOKEN")
TG_ID = os.getenv("TG_ID")

RENEW_ACTION_URL = "https://new.freemchost.com/_serverFn/798181797bd95a02dee916a26c18d3539a58152db8660e097ca48d7cdd8ee50c"
RENEW_DETAIL_URL = "https://new.freemchost.com/_serverFn/c3a45c08362f2f613bbb6d511a3733a9e85e561709d48bec9280e82a4aa4f47d"
SERVER_ID = "82f18f00-8d41-49e0-9b33-a4c8c6dd1faa"

if not all([EMAIL, PASSWORD, SUPABASE_ANON_KEY, TG_TOKEN, TG_ID]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 🛑 错误: 缺少必要的环境变量 (检查 Email, Password, Key, TG_TOKEN, TG_ID)。")
    sys.exit(1)
# =====================================================

def log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")

def notify(title, content):
    """通过 Telegram Bot API 推送消息"""
    msg = f"*{title}*\n\n{content}"
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
        log("✅ Telegram 通知发送成功")
    except Exception as e:
        log(f"🔔 Telegram 推送通知失败: {e}")

def parse_action_response(res_json):
    action_info = {"expires_at": None, "status_code": "未知"}
    try:
        outer_p = res_json.get("p", {})
        keys = outer_p.get("k", [])
        values = outer_p.get("v", [])
        if "result" in keys:
            idx = keys.index("result")
            result_node_p = values[idx].get("p", {})
            sub_keys = result_node_p.get("k", [])
            sub_values = result_node_p.get("v", [])
            if "expires_at" in sub_keys:
                action_info["expires_at"] = sub_values[sub_keys.index("expires_at")].get("s")
        if "error" in keys:
            action_info["status_code"] = values[keys.index("error")].get("s", "未知")
    except Exception as e:
        log(f"解析续期动作响应异常: {e}")
    return action_info

def parse_detail_response(res_json):
    info = {"name": "未知", "status": "未知"}
    try:
        outer_v = res_json.get("p", {}).get("v", [])
        if outer_v:
            mid_v = outer_v[0].get("p", {}).get("v", [])
            if mid_v:
                server_node = mid_v[0]
                keys = server_node.get("p", {}).get("k", [])
                values = server_node.get("p", {}).get("v", [])
                if "name" in keys: info["name"] = values[keys.index("name")].get("s", "未知")
                if "status" in keys: info["status"] = values[keys.index("status")].get("s", "未知")
    except Exception as e:
        log(f"解析最终详情响应异常: {e}")
    return info

def get_new_token():
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "content-type": "application/json"
    }
    payload = {"email": EMAIL, "password": PASSWORD, "gotrue_meta_security": {}}
    try:
        response = requests.post(LOGIN_URL, headers=headers, json=payload, timeout=10)
        return response.json().get("access_token") if response.status_code == 200 else None
    except:
        return None

def run_auto_renew():
    token = get_new_token()
    if not token:
        notify("服务器自动续期失败", "模拟登录获取 Token 失败。")
        sys.exit(1)

    base_headers = {"authorization": f"Bearer {token}", "content-type": "application/json", "x-tsr-serverfn": "true"}
    renew_payload = {"t": {"t": 10, "i": 0, "p": {"k": ["data"], "v": [{"t": 10, "i": 1, "p": {"k": ["id"], "v": [{"t": 1, "s": SERVER_ID}]}, "o": 0}]}}, "f": 63, "m": []}

    action_res = requests.post(RENEW_ACTION_URL, headers=base_headers, json=renew_payload, timeout=15)
    action_info = parse_action_response(action_res.json()) if action_res.status_code == 200 else {}
    
    expires_at = action_info.get("expires_at")
    if not expires_at:
        notify("服务器自动续期失败", "续期接口未返回有效期。")
        sys.exit(1)

    detail_res = requests.post(RENEW_DETAIL_URL, headers=base_headers, json=renew_payload, timeout=15)
    server_info = parse_detail_response(detail_res.json()) if detail_res.status_code == 200 else {"name": "未知", "status": "未知"}

    msg_content = f"服务器: {server_info['name']}\n状态: {server_info['status']}\n到期时间: {expires_at}"
    log(msg_content)
    notify("服务器自动续期成功", msg_content)

if __name__ == "__main__":
    run_auto_renew()
