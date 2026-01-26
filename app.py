import os
import time
import threading
import requests
from flask import Flask
from telegram import Bot, InputFile
from telegram.error import TelegramError, RetryAfter

app = Flask(__name__)

# ==================== 配置（优先从环境变量读取） ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8536915783:AAE-UrQYYlpsUJ4Syho0zSGUMKifTdjRlLU")
BASE_URL = os.getenv("BASE_URL", "https://prominent-tootsie-apkrelease-1850e28f.koyeb.app/bot")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@你的频道用户名")  # 必须改成你的真实频道

GITHUB_REPO = "FongMi/Release"
BRANCH = "fongmi"
FOLDER = "apk"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FOLDER}?ref={BRANCH}"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{FOLDER}/"

CHECK_INTERVAL = 6 * 3600  # 每6小时检查一次（秒）

bot = Bot(token=BOT_TOKEN, base_url=BASE_URL)

def send_all_apks():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始检查 APK...")
    
    headers = {
        'User-Agent': 'Render-APK-Pusher/1.0'
    }
    if os.getenv("GITHUB_TOKEN"):
        headers['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"
        headers['Accept'] = "application/vnd.github.v3+json"
        print("使用 GitHub Token 认证（匿名限速已绕过）")
    else:
        print("警告：未设置 GITHUB_TOKEN，使用匿名请求，容易被限速")

    try:
        resp = requests.get(GITHUB_API_URL, headers=headers, timeout=20)
        print(f"GitHub API 响应码: {resp.status_code}")  # 调试用
        resp.raise_for_status()
        files = resp.json()
    except Exception as e:
        print(f"获取 GitHub 失败: {str(e)}")
        if 'resp' in locals():
            print(f"响应文本: {resp.text}")
        return

    apks = [f for f in files if f.get('type') == 'file' and f['name'].lower().endswith('.apk')]
    if not apks:
        print("未找到 APK")
        return

    print(f"找到 {len(apks)} 个 APK: {[f['name'] for f in apks]}")

    for apk in apks:
        name = apk['name']
        url = RAW_BASE_URL + name
        size_mb = apk['size'] / (1024 * 1024)

        print(f"正在发送: {name} ({size_mb:.1f} MB)")

        try:
            r = requests.get(url, stream=True, timeout=120)
            r.raise_for_status()

            bot.send_document(
                chat_id=CHANNEL_ID,
                document=InputFile(r.raw, filename=name),
                caption=f"【FongMi Release 更新】\n文件名: {name}\n大小: {size_mb:.1f} MB\n来源: {url}",
                timeout=600
            )

            print(f"成功发送: {name}")
            time.sleep(8)  # 防 Telegram 限速

        except RetryAfter as ra:
            print(f"限速，等待 {ra.retry_after + 10} 秒")
            time.sleep(ra.retry_after + 10)
        except Exception as e:
            print(f"失败 {name}: {e}")

def background_loop():
    while True:
        send_all_apks()
        print(f"等待下次检查 ({CHECK_INTERVAL // 3600} 小时)...")
        time.sleep(CHECK_INTERVAL)

@app.route('/')
@app.route('/health')
def health():
    return "OK - APK Pusher is running", 200

if __name__ == "__main__":
    print("启动 APK 推送服务...")
    # 启动后台推送线程
    threading.Thread(target=background_loop, daemon=True).start()
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
