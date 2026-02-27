import requests
import os
from datetime import datetime
from tqdm import tqdm

# ---------------- 配置 ----------------
STD_BASE = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视标准版"
PRO_BASE = "https://op.ll.dovx.cf/d/APP/OK影视/OK影视Pro"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 标准版和Pro版APK对应改名
STD_APK_MAP = {
    "海信专版": "hisense-tv-universal-ok.apk",
    "leanback-arm64_v8a": "leanback-arm64_v8a-ok.apk",
    "leanback-armeabi_v7a": "leanback-armeabi_v7a-ok.apk",
    "mobile-arm64_v8a": "mobile-arm64_v8a-ok.apk",
    "mobile-armeabi_v7a": "mobile-armeabi_v7a-ok.apk",
}

PRO_APK_MAP = {
    "leanback-armeabi_v7a": "leanback-armeabi_v7a-pro.apk",
    "leanback-arm64_v8a": "leanback-arm64_v8a-pro.apk",
    "mobile-armeabi_v7a": "mobile-armeabi_v7a-pro.apk",
    "mobile-arm64_v8a": "mobile-arm64_v8a-pro.apk",
}

# ---------------- 工具函数 ----------------
def probe_latest_version(base_url, start_ver, keyword):
    """从 start_ver 开始递增版本号探测最新版本"""
    major, minor, patch = map(int, start_ver.split("."))
    latest = None
    for i in range(0, 30):  # 最多探30个patch
        ver = f"{major}.{minor}.{patch + i}"
        txt_url = f"{base_url}/{ver}/{keyword}{ver}.txt"
        r = requests.head(txt_url, allow_redirects=True)
        if r.status_code == 200:
            latest = ver
        else:
            if latest:
                break
    if not latest:
        raise Exception(f"未找到 {keyword} 最新版本")
    return latest

def download_file(url, out_path):
    """下载文件到指定路径，支持带 sign= 的直链"""
    r = requests.get(url, stream=True, allow_redirects=True)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    with open(out_path, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=os.path.basename(out_path)
    ) as pbar:
        for chunk in r.iter_content(8192):
            f.write(chunk)
            pbar.update(len(chunk))

def fetch_version(base_url, apk_map, keyword, start_ver):
    """探测最新版本并下载 APK"""
    print(f"\n==== 下载 {keyword} ====")
    latest_ver = probe_latest_version(base_url, start_ver, keyword)
    print(f"{keyword} 最新版本: {latest_ver}")

    files = []
    caption_lines = [f"{keyword} 自动更新", f"本次版本: {latest_ver}"]

    for key, name in apk_map.items():
        # 构造 TXT 文件路径，获取真实下载URL
        txt_name = f"{key}-{latest_ver}.apk" if 'Pro' not in keyword else f"OK影视Pro-{key}-{latest_ver}.apk"
        txt_url = f"{base_url}/{latest_ver}/{txt_name}"

        # 用 HEAD 获取真实下载直链
        r = requests.head(txt_url, allow_redirects=True)
        if r.status_code != 200:
            print(f"跳过 {txt_name}, 状态码: {r.status_code}")
            continue

        real_url = r.url
        out_path = os.path.join(DOWNLOAD_DIR, name)
        print(f"下载 {real_url} -> {out_path}")
        download_file(real_url, out_path)
        files.append(name)

    # 保存 caption.txt
    caption_path = os.path.join(DOWNLOAD_DIR, f"{keyword.replace(' ', '_')}_caption.txt")
    caption_lines.append(f"更新时间: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write("\n".join(caption_lines))

    return latest_ver, files, caption_path

# ---------------- 主程序 ----------------
def main():
    std_ver, std_files, std_caption = fetch_version(STD_BASE, STD_APK_MAP, "OK影视 标准版", "3.7.0")
    pro_ver, pro_files, pro_caption = fetch_version(PRO_BASE, PRO_APK_MAP, "OK影视 Pro版", "5.0.1")

    print("\n==== 下载完成 ====")
    print(f"标准版文件: {std_files}, caption: {std_caption}")
    print(f"Pro版文件: {pro_files}, caption: {pro_caption}")

if __name__ == "__main__":
    main()
