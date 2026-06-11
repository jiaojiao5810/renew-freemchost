import os
import sys
from datetime import datetime
import requests

# ==================== 🔧 核心配置区 ====================
# 1. 登录配置
LOGIN_URL = "https://laehfeigoiycigkfknfn.supabase.co/auth/v1/token?grant_type=password"
EMAIL = os.getenv("MY_EMAIL")
PASSWORD = os.getenv("MY_PASSWORD")
SUPABASE_ANON_KEY = os.getenv("ANON_KEY")

# 2. 路由配置
RENEW_ACTION_URL = "https://new.freemchost.com/_serverFn/798181797bd95a02dee916a26c18d3539a58152db8660e097ca48d7cdd8ee50c"
RENEW_DETAIL_URL = "https://new.freemchost.com/_serverFn/c3a45c08362f2f613bbb6d511a3733a9e85e561709d48bec9280e82a4aa4f47d"
SERVER_ID = "82f18f00-8d41-49e0-9b33-a4c8c6dd1faa"

# 3. Telegram 推送配置
TG_BOT_TOKEN = os.getenv("8809031806:AAGs7s77eKSalcshs1t6WheM8iGrma6k_WI8809031806:AAGs7s77eKSalcshs1t6WheM8iGrma6k_WI")
TG_CHAT_ID = os.getenv("7711153850")

# 🚨 安全校验
if not all([EMAIL, PASSWORD, SUPABASE_ANON_KEY, TG_BOT_TOKEN, TG_CHAT_ID]):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 🛑 错误: 缺少必要的环境变量 (检查 EMAIL, PASSWORD, ANON_KEY, TG_BOT_TOKEN, TG_CHAT_ID)")
    sys.exit(1)
# =====================================================

def log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")

def notify(title, content):
    """通过 Telegram Bot 推送通知"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": f"🔔 {title}\n\n{content}",
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=5)
        log("✅ Telegram 推送已发送")
    except Exception as e:
        log(f"🔔 Telegram 推送失败: {e}")

def parse_action_response(res_json):
    action_info = {"expires_at": None, "status_code": "未知"}
    try:
        outer_p = res_json.get("p", {})
        keys = outer_p.get("k", [])
        values = outer_p.get("v", [])
        if "result" in keys:
            idx = keys.index("result")
            sub_keys = values[idx].get("p", {}).get("k", [])
            sub_values = values[idx].get("p", {}).get("v", [])
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
        server_node = outer_v[0].get("p", {}).get("v", [])[0]
        keys = server_node.get("p", {}).get("k", [])
        values = server_node.get("p", {}).get("v", [])
        if "name" in keys: info["name"] = values[keys.index("name")].get("s", "未知")
        if "status" in keys: info["status"] = values[keys.index("status")].get("s", "未知")
    except Exception as e:
        log(f"解析详情响应异常: {e}")
    return info

def get_new_token():
    log("🔑 正在获取 Token...")
    headers = {"apikey": SUPABASE_ANON_KEY, "authorization": f"Bearer {SUPABASE_ANON_KEY}", "content-type": "application/json"}
    payload = {"email": EMAIL, "password": PASSWORD}
    try:
        response = requests.post(LOGIN_URL, headers=headers, json=payload, timeout=10)
        return response.json().get("access_token") if response.status_code == 200 else None
    except:
        return None

def run_auto_renew():
    token = get_new_token()
    if not token:
        notify("服务器自动续期失败", "无法获取 Token，请检查账号密码。")
        sys.exit(1)

    base_headers = {"authorization": f"Bearer {token}", "content-type": "application/json", "x-tsr-serverfn": "true"}
    renew_payload = {"t": {"t": 10, "i": 0, "p": {"k": ["data"], "v": [{"t": 10, "i": 1, "p": {"k": ["id"], "v": [{"t": 1, "s": SERVER_ID}]}, "o": 0}]}}, "f": 63, "m": []}

    # 续期执行
    action_res = requests.post(RENEW_ACTION_URL, headers=base_headers, json=renew_payload, timeout=15)
    action_info = parse_action_response(action_res.json())
    
    if not action_info["expires_at"]:
        notify("服务器自动续期失败", f"接口未返回过期时间，状态码: {action_info['status_code']}")
        sys.exit(1)

    # 获取详情
    detail_res = requests.post(RENEW_DETAIL_URL, headers=base_headers, json=renew_payload, timeout=15)
    server_info = parse_detail_response(detail_res.json())

    log("🎉 续期完成")
    notify(
        "服务器自动续期成功", 
        f"服务器: {server_info['name']}\n状态: {server_info['status']}\n新到期时间: {action_info['expires_at']}"
    )

if __name__ == "__main__":
    run_auto_renew()
