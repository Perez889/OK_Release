import os
import re
import requests
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# ===== 配置 =====
BASE_PRO = "https://op.ll.dovx.cf/OK影视/OK影视Pro/"
BASE_STD = "https://op.ll.dovx.cf/OK影视/OK影视标准版/"
OUT_DIR = "apk"
os.makedirs(OUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# ===== 下载函数 =====
def download(url, filename):
    print("下载:", filename)
    r = session.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(os.path.join(OUT_DIR, filename), "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

# ===== Pro 版获取最新版本 =====
def get_pro_latest_version():
    r = session.get(BASE_PRO, timeout=30)
    r.raise_for_status()
    # 匹配 OK影视Pro-电视版-32位-5.0.1.apk 中的版本号
    versions = re.findall(r'OK影视Pro-电视版-32位-(\d+\.\d+\.\d+)\.apk', r.text)
    if not versions:
        raise RuntimeError("未找到 Pro 版本")
    versions.sort(key=lambda v: list(map(int, v.split("."))))
    return versions[-1]

# ===== Pro 版下载 =====
def fetch_pro():
    version = get_pro_latest_version()
    folder = BASE_PRO + version + "/"

    mapping = {
        f"OK影视Pro-电视版-32位-{version}.apk": "leanback-armeabi_v7a-pro.apk",
        f"OK影视Pro-电视版-64位-{version}.apk": "leanback-arm64_v8a-pro.apk",
        f"OK影视Pro-手机版-{version} - 模拟器.apk": "mobile-armeabi_v7a-pro.apk",
        f"OK影视Pro-手机版-{version}.apk": "mobile-arm64_v8a-pro.apk",
    }

    for src, dst in mapping.items():
        download(folder + quote(src), dst)

    return version

# ===== 标准版获取最新版本 =====
def get_std_latest_folder():
    r = session.get(BASE_STD, timeout=30)
    r.raise_for_status()
    # 匹配 x.x.x/ 目录
    versions = re.findall(r'href="(\d+\.\d+\.\d+)/"', r.text)
    if not versions:
        raise RuntimeError(f"未找到标准版目录: {BASE_STD}")
    versions.sort(key=lambda v: list(map(int, v.split("."))))
    return versions[-1]

# ===== 标准版下载 =====
def fetch_standard():
    version = get_std_latest_folder()
    folder = BASE_STD + version + "/"

    mapping = {
        f"海信专版-OK影视-{version}.apk": "hisense-tv-universal-ok.apk",
        f"leanback-arm64_v8a-{version}.apk": "leanback-arm64_v8a-ok.apk",
        f"leanback-armeabi_v7a-{version}.apk": "leanback-armeabi_v7a-ok.apk",
        f"mobile-arm64_v8a-{version}.apk": "mobile-arm64_v8a-ok.apk",
        f"mobile-armeabi_v7a-{version}.apk": "mobile-armeabi_v7a-ok.apk",
    }

    for src, dst in mapping.items():
        download(folder + quote(src), dst)

    return version

# ===== 获取标准版更新日志 =====
def fetch_update_log(version):
    url = f"{BASE_STD}{version}/标准版{version}.txt"
    r = session.get(url, timeout=30)
    if r.status_code != 200 or not r.text.strip():
        return "暂无更新日志"

    logs = []
    for line in r.text.splitlines():
        line = line.strip().lstrip("*").strip()
        if line:
            logs.append(f"• {line}")

    return "\n".join(sorted(set(logs)))

# ===== 生成 caption =====
def generate_caption(std_v, pro_v, logs):
    beijing = datetime.now(timezone(timedelta(hours=8)))
    time_str = beijing.strftime("%Y/%m/%d %H:%M")

    caption = f"""
OK影视自动更新

本次更新：
{logs}

标准版：{std_v}
Pro版：{pro_v}
更新时间：{time_str}
""".strip()

    with open("caption.txt", "w", encoding="utf-8") as f:
        f.write(caption)

    with open("latest_version.txt", "w") as f:
        f.write(f"Pro:{pro_v}\nStd:{std_v}")

    print(caption)

# ===== 主函数 =====
def main():
    pro_v = fetch_pro()
    std_v = fetch_standard()
    logs = fetch_update_log(std_v)
    generate_caption(std_v, pro_v, logs)
    print("全部完成")

if __name__ == "__main__":
    main()
