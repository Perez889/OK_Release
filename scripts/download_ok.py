import os
import re
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import unquote

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 基础 TXT 文件 URL 列表页面
STD_LIST_URL = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视标准版/"
PRO_LIST_URL = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视Pro/"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_latest_txt(list_url, keyword="标准版"):
    """抓取最新 TXT 文件 URL"""
    r = requests.get(list_url, headers=HEADERS)
    if r.status_code != 200:
        raise Exception(f"无法访问 {list_url}")
    # 抓所有 TXT 链接
    links = re.findall(r'https://[^\s]+?\.txt[^\s]*', r.text)
    # 只保留匹配关键字的
    filtered = [l for l in links if keyword in l]
    if not filtered:
        raise Exception(f"未找到 {keyword} TXT 文件")
    # 按版本号排序（假设版本号形式是 x.y.z）
    def ver_key(url):
        m = re.search(r'(\d+\.\d+\.\d+)', url)
        return [int(x) for x in m.group(1).split('.')] if m else [0,0,0]
    filtered.sort(key=ver_key)
    latest = filtered[-1]
    return unquote(latest)

def extract_apk_links(txt_url):
    r = requests.get(txt_url, headers=HEADERS)
    if r.status_code != 200:
        raise Exception(f"未找到 TXT 文件: {txt_url}")
    urls = re.findall(r"https://[^\s]+?\.apk[^\s]*", r.text)
    return [unquote(u) for u in urls]

def extract_update_log(txt_url):
    r = requests.get(txt_url, headers=HEADERS)
    if r.status_code != 200:
        return "无更新日志"
    lines = r.text.splitlines()
    bullets = []
    for line in lines:
        line = line.strip()
        if line:
            bullets.append(f"• {line}")
    return "\n".join(bullets) if bullets else "无更新日志"

def download_files(urls, mapping):
    downloaded = []
    for url in urls:
        for key, name in mapping.items():
            if key in url:
                path = os.path.join(DOWNLOAD_DIR, name)
                print("下载:", name)
                r = requests.get(url, headers=HEADERS, stream=True)
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                downloaded.append(name)
    return downloaded

def generate_caption(std_ver, pro_ver, std_log, pro_log):
    beijing = datetime.now(timezone(timedelta(hours=8)))
    ts = beijing.strftime("%Y/%m/%d %H:%M")
    caption_std = f"📢 OK影视 标准版更新\n版本: {std_ver}\n更新时间: {ts}\n更新日志:\n{std_log}"
    caption_pro = f"📢 OK影视 Pro版更新\n版本: {pro_ver}\n更新时间: {ts}\n更新日志:\n{pro_log}"
    with open("caption_std.txt", "w", encoding="utf-8") as f:
        f.write(caption_std)
    with open("caption_pro.txt", "w", encoding="utf-8") as f:
        f.write(caption_pro)
    with open("latest_version.txt", "w", encoding="utf-8") as f:
        f.write(f"Std:{std_ver}\nPro:{pro_ver}")
    return caption_std, caption_pro

def main():
    # 标准版
    std_txt_url = get_latest_txt(STD_LIST_URL, "标准版")
    std_ver = re.search(r'(\d+\.\d+\.\d+)', std_txt_url).group(1)
    std_links = extract_apk_links(std_txt_url)
    std_log = extract_update_log(std_txt_url)
    std_map = {
        "海信专版": "hisense-tv-universal-ok.apk",
        "leanback-arm64_v8a": "leanback-arm64_v8a-ok.apk",
        "leanback-armeabi_v7a": "leanback-armeabi_v7a-ok.apk",
        "mobile-arm64_v8a": "mobile-arm64_v8a-ok.apk",
        "mobile-armeabi_v7a": "mobile-armeabi_v7a-ok.apk",
    }
    download_files(std_links, std_map)

    # Pro版
    pro_txt_url = get_latest_txt(PRO_LIST_URL, "Pro版")
    pro_ver = re.search(r'(\d+\.\d+\.\d+)', pro_txt_url).group(1)
    pro_links = extract_apk_links(pro_txt_url)
    pro_log = extract_update_log(pro_txt_url)
    pro_map = {
        "电视版-32位": "leanback-armeabi_v7a-pro.apk",
        "电视版-64位": "leanback-arm64_v8a-pro.apk",
        "手机版 - 模拟器": "mobile-armeabi_v7a-pro.apk",
        "手机版": "mobile-arm64_v8a-pro.apk",
    }
    download_files(pro_links, pro_map)

    generate_caption(std_ver, pro_ver, std_log, pro_log)
    print("下载完成，生成 caption 和 latest_version.txt")

if __name__ == "__main__":
    main()
