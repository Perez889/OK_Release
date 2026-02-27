import requests
import re
import os
from urllib.parse import unquote
from datetime import datetime

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 标准版 / Pro 版目录
STD_BASE = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视标准版/"
PRO_BASE = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视Pro/"

# 下载函数
def download(url, filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    print(f"下载: {url} -> {filename}")
    r = requests.get(url, headers=HEADERS, stream=True, timeout=60)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

# 获取最新标准版版本号
def get_latest_std_version():
    html = requests.get(STD_BASE, headers=HEADERS).text
    versions = re.findall(r'>(\d+\.\d+\.\d+)/<', html)
    versions.sort(key=lambda v: list(map(int, v.split('.'))))
    if not versions:
        raise RuntimeError("未找到标准版版本")
    return versions[-1]

# 获取最新 Pro 版版本号
def get_latest_pro_version():
    html = requests.get(PRO_BASE, headers=HEADERS).text
    versions = re.findall(r'Pro版(\d+\.\d+\.\d+)\.txt', html)
    versions.sort(key=lambda v: list(map(int, v.split('.'))))
    if not versions:
        raise RuntimeError("未找到 Pro 版本")
    return versions[-1]

# 提取 txt 中的 APK 链接
def extract_links(txt_url):
    text = requests.get(txt_url, headers=HEADERS).text
    urls = re.findall(r"https://[^\s]+?\.apk[^\s]*", text)
    return [unquote(u) for u in urls]

# 下载标准版
def fetch_std():
    print("==== 下载标准版 ====")
    version = get_latest_std_version()
    txt_url = f"{STD_BASE}{version}/标准版{version}.txt"
    links = extract_links(txt_url)

    mapping = {
        "海信专版": "hisense-tv-universal-ok.apk",
        "leanback-arm64_v8a": "leanback-arm64_v8a-ok.apk",
        "leanback-armeabi_v7a": "leanback-armeabi_v7a-ok.apk",
        "mobile-arm64_v8a": "mobile-arm64_v8a-ok.apk",
        "mobile-armeabi_v7a": "mobile-armeabi_v7a-ok.apk",
    }

    for url in links:
        for key, name in mapping.items():
            if key in url:
                download(url, name)
    return version

# 下载 Pro 版
def fetch_pro():
    print("==== 下载 Pro版 ====")
    version = get_latest_pro_version()
    txt_url = f"{PRO_BASE}Pro版{version}.txt"
    links = extract_links(txt_url)

    # Pro 固定 4 个文件名
    mapping = {
        "电视版-32位": "leanback-armeabi_v7a-pro.apk",
        "电视版-64位": "leanback-arm64_v8a-pro.apk",
        "手机版 - 模拟器": "mobile-armeabi_v7a-pro.apk",
        "手机版": "mobile-arm64_v8a-pro.apk",
    }

    for url in links:
        for key, name in mapping.items():
            if key in url:
                download(url, name)
    return version

# 生成 caption
def make_caption(std_ver, pro_ver):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    caption = f"""📢 OK影视 自动更新

标准版：{std_ver}
Pro版：{pro_ver}
更新时间：{now}

#OK影视 #自动更新
"""
    with open("caption.txt", "w", encoding="utf-8") as f:
        f.write(caption)

def main():
    std_ver = fetch_std()
    pro_ver = fetch_pro()
    make_caption(std_ver, pro_ver)
    print("全部完成")

if __name__ == "__main__":
    main()
