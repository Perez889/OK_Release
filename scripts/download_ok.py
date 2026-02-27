import os
import re
import requests
from datetime import datetime, timezone, timedelta

# ---------- 配置区域 ----------
STD_TXT_URL = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视标准版/3.7.0/标准版3.7.0.txt?sign=XXX"
PRO_TXT_URL = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视Pro/Pro版5.0.1.txt?sign=XXX"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# APK 改名规则
STD_MAP = {
    "海信专版-OK影视": "hisense-tv-universal-ok.apk",
    "leanback-arm64_v8a": "leanback-arm64_v8a-ok.apk",
    "leanback-armeabi_v7a": "leanback-armeabi_v7a-ok.apk",
    "mobile-arm64_v8a": "mobile-arm64_v8a-ok.apk",
    "mobile-armeabi_v7a": "mobile-armeabi_v7a-ok.apk",
}

PRO_MAP = {
    "OK影视Pro-电视版-32位": "leanback-armeabi_v7a-pro.apk",
    "OK影视Pro-电视版-64位": "leanback-arm64_v8a-pro.apk",
    "OK影视Pro-手机版-模拟器": "mobile-armeabi_v7a-pro.apk",
    "OK影视Pro-手机版": "mobile-arm64_v8a-pro.apk",
}

# Telegram 配置
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
BOT_API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org")

# ---------- 辅助函数 ----------
def fetch_txt(txt_url):
    r = requests.get(txt_url, timeout=30)
    r.raise_for_status()
    return r.text

def parse_apk_links(txt_content):
    """提取 TXT 文件中的 APK 直链"""
    urls = re.findall(r"https?://\S+\.apk\S*", txt_content)
    return urls

def download_apk(url, filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(path):
        print(f"已存在，跳过 {filename}")
        return
    print(f"下载 {filename} -> {url}")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

def generate_caption(version, logs, name="OK影视"):
    beijing = datetime.now(timezone(timedelta(hours=8)))
    time_str = beijing.strftime("%Y/%m/%d %H:%M")
    caption = f"{name} 自动更新\n版本：{version}\n更新时间：{time_str}\n本次更新：\n{logs}"
    return caption

def send_telegram(files, caption=None):
    import json
    media = []
    for f in files[:-1]:
        media.append({"type": "document", "media": f"attach://{f}"})
    media.append({"type": "document", "media": f"attach://{files[-1]}", "caption": caption or ""})
    data = {
        "chat_id": CHAT_ID,
        "media": json.dumps(media)
    }
    files_payload = {f: open(os.path.join(DOWNLOAD_DIR, f), "rb") for f in files}
    r = requests.post(f"{BOT_API_BASE}/bot{BOT_TOKEN}/sendMediaGroup", data=data, files=files_payload)
    print("Telegram 响应:", r.text)
    for f in files:
        files_payload[f].close()

# ---------- 主逻辑 ----------
def process_version(txt_url, apk_map, name="OK影视"):
    txt_content = fetch_txt(txt_url)
    version_match = re.search(r"\d+\.\d+\.\d+", txt_content)
    version = version_match.group() if version_match else "未知版本"
    logs = "\n".join([f"• {line.strip('* ')}" for line in txt_content.splitlines() if line.strip()])
    caption = generate_caption(version, logs, name)
    
    urls = parse_apk_links(txt_content)
    files = []
    for url in urls:
        for key in apk_map:
            if key in url:
                filename = apk_map[key]
                download_apk(url, filename)
                files.append(filename)
                break
    return version, files, caption

def main():
    # 标准版
    print("==== 下载标准版 ====")
    std_ver, std_files, std_caption = process_version(STD_TXT_URL, STD_MAP, "OK影视 标准版")
    print(std_caption)
    send_telegram(std_files, std_caption)

    # Pro版
    print("==== 下载 Pro 版 ====")
    pro_ver, pro_files, pro_caption = process_version(PRO_TXT_URL, PRO_MAP, "OK影视 Pro版")
    print(pro_caption)
    send_telegram(pro_files, pro_caption)

if __name__ == "__main__":
    main()
