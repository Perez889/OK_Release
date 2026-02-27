import os
import re
import requests
from urllib.parse import urljoin, quote
from datetime import datetime, timezone, timedelta

# 基础目录
STD_BASE_PAGE = "https://op.ll.dovx.cf/OK影视/OK影视标准版/"
PRO_BASE_PAGE = "https://op.ll.dovx.cf/OK影视/OK影视Pro/"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def fetch_html(url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def get_latest_txt_url(base_page, keyword="标准版"):
    """从目录 HTML 中获取最新 TXT 文件 URL"""
    html = fetch_html(base_page)
    # 匹配 txt 文件 href
    matches = re.findall(r'href="([^"]+\.txt\?sign=[^"]+)"', html)
    if not matches:
        raise Exception(f"无法从目录获取 {keyword} TXT")
    # 按版本号排序（取最后一个）
    matches.sort(key=lambda x: [int(i) for i in re.findall(r"(\d+)", x)])
    latest_txt = urljoin(base_page, matches[-1])
    return latest_txt


def fetch_txt(url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def parse_apk_links(txt_content, base_page):
    """从 TXT 内容中匹配所有 APK 直连"""
    # 匹配 .apk?sign= 的 URL
    urls = re.findall(r'https://op\.ll\.dovx\.cf[^\s"]+\.apk\?sign=[^"\s]+', txt_content)
    return urls


def download_file(url, filename):
    path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(path):
        print(f"{filename} 已存在，跳过下载")
        return
    print(f"下载 {filename} -> {path}")
    r = session.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)


def process_version(base_page, apk_map, keyword):
    txt_url = get_latest_txt_url(base_page, keyword)
    txt_content = fetch_txt(txt_url)

    # 提取版本号
    ver_match = re.search(r"(\d+\.\d+\.\d+)", txt_url)
    version = ver_match.group(1) if ver_match else "未知版本"

    apk_urls = parse_apk_links(txt_content, base_page)

    downloaded_files = []
    for url in apk_urls:
        # 根据 APK 原名匹配新名
        filename = url.split("/")[-1].split("?")[0]
        new_name = apk_map.get(filename, filename)
        download_file(url, new_name)
        downloaded_files.append(new_name)

    # 生成 caption
    beijing = datetime.now(timezone(timedelta(hours=8)))
    time_str = beijing.strftime("%Y/%m/%d %H:%M")
    caption_lines = []
    for line in txt_content.splitlines():
        line = line.strip().lstrip("*").strip()
        if line:
            caption_lines.append(f"• {line}")
    caption = "\n".join(caption_lines) or "暂无更新日志"
    caption_full = f"{keyword} 自动更新\n本次更新：\n{caption}\n版本：{version}\n更新时间：{time_str}"

    return version, downloaded_files, caption_full


def main():
    print("==== 下载标准版 ====")
    STD_MAP = {
        "海信专版-OK影视-3.7.0.apk": "hisense-tv-universal-ok.apk",
        "leanback-arm64_v8a-3.7.0.apk": "leanback-arm64_v8a-ok.apk",
        "leanback-armeabi_v7a-3.7.0.apk": "leanback-armeabi_v7a-ok.apk",
        "mobile-arm64_v8a-3.7.0.apk": "mobile-arm64_v8a-ok.apk",
        "mobile-armeabi_v7a-3.7.0.apk": "mobile-armeabi_v7a-ok.apk",
    }
    std_ver, std_files, std_caption = process_version(STD_BASE_PAGE, STD_MAP, "OK影视 标准版")

    with open("caption_std.txt", "w", encoding="utf-8") as f:
        f.write(std_caption)

    print("\n==== 下载 Pro 版 ====")
    PRO_MAP = {
        "OK影视Pro-电视版-32位-5.0.1.apk": "leanback-armeabi_v7a-pro.apk",
        "OK影视Pro-电视版-64位-5.0.1.apk": "leanback-arm64_v8a-pro.apk",
        "OK影视Pro-手机版-5.0.1.apk": "mobile-arm64_v8a-pro.apk",
        "OK影视Pro-手机版-5.0.1 - 模拟器.apk": "mobile-armeabi_v7a-pro.apk",
    }
    pro_ver, pro_files, pro_caption = process_version(PRO_BASE_PAGE, PRO_MAP, "OK影视 Pro版")

    with open("caption_pro.txt", "w", encoding="utf-8") as f:
        f.write(pro_caption)

    print("\n标准版文件:", std_files)
    print("Pro版文件:", pro_files)
    print("\n标准版 caption:", std_caption)
    print("\nPro版 caption:", pro_caption)


if __name__ == "__main__":
    main()
