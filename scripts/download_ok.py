import os
import requests
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# ==== 配置 ====
OK_STD_BASE = "https://op.ll.dovx.cf/OK影视/OK影视标准版"
OK_PRO_BASE = "https://op.ll.dovx.cf/OK影视/OK影视Pro"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==== 工具函数 ====
def download_file(url, local_name):
    """下载文件到 DOWNLOAD_DIR"""
    path = os.path.join(DOWNLOAD_DIR, local_name)
    print(f"下载 {url} -> {path}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return path

def fetch_latest_std_version():
    """探测标准版最新版本"""
    major, minor = 3, 7
    for patch in range(0, 30):
        ver = f"{major}.{minor}.{patch}"
        txt_url = f"{OK_STD_BASE}/{ver}/标准版{ver}.txt"
        r = requests.get(txt_url)
        if r.status_code == 200 and len(r.text.strip()) > 0:
            latest = ver
        else:
            if patch > 0:
                break
    if not latest:
        raise Exception("未找到最新标准版")
    return latest

def fetch_latest_pro_version():
    """探测 Pro 版最新版本"""
    # Pro 版没有 txt，直接用固定版本号或可按实际情况硬编码
    # 这里尝试 5.0.0~5.0.5
    for patch in range(0, 10):
        ver = f"5.0.{patch}"
        # 直接尝试是否有 32位 APK
        url = f"{OK_PRO_BASE}/OK影视Pro-电视版-32位-{ver}.apk"
        r = requests.head(url)
        if r.status_code == 200:
            latest = ver
        else:
            if patch > 0:
                break
    if not latest:
        raise Exception("未找到最新 Pro 版")
    return latest

def parse_update_log(version):
    """获取标准版 txt 更新日志"""
    url = f"{OK_STD_BASE}/{version}/标准版{version}.txt"
    r = requests.get(url)
    if r.status_code != 200 or not r.text.strip():
        return "暂无更新日志"
    logs = []
    for line in r.text.splitlines():
        line = line.strip().lstrip("*").strip()
        if line:
            logs.append(f"• {line}")
    return "\n".join(sorted(set(logs)))

# ==== 下载标准版 ====
def download_std(version):
    base = f"{OK_STD_BASE}/{version}/"
    files = {
        f"海信专版-OK影视-{version}.apk": "hisense-tv-universal-ok.apk",
        f"leanback-arm64_v8a-{version}.apk": "leanback-arm64_v8a-ok.apk",
        f"leanback-armeabi_v7a-{version}.apk": "leanback-armeabi_v7a-ok.apk",
        f"mobile-arm64_v8a-{version}.apk": "mobile-arm64_v8a-ok.apk",
        f"mobile-armeabi_v7a-{version}.apk": "mobile-armeabi_v7a-ok.apk",
    }
    paths = []
    for remote, local in files.items():
        url = base + quote(remote)
        try:
            download_file(url, local)
            paths.append(local)
        except:
            print("跳过:", remote)
    return paths

# ==== 下载 Pro 版 ====
def download_pro(version):
    base = f"{OK_PRO_BASE}/"
    files = {
        f"OK影视Pro-电视版-32位-{version}.apk": "leanback-armeabi_v7a-pro.apk",
        f"OK影视Pro-电视版-64位-{version}.apk": "leanback-arm64_v8a-pro.apk",
        f"OK影视Pro-手机版-{version} - 模拟器.apk": "mobile-armeabi_v7a-pro.apk",
        f"OK影视Pro-手机版-{version}.apk": "mobile-arm64_v8a-pro.apk",
    }
    paths = []
    for remote, local in files.items():
        url = base + quote(remote)
        try:
            download_file(url, local)
            paths.append(local)
        except:
            print("跳过:", remote)
    return paths

# ==== 生成 Telegram caption ====
def generate_caption(version, logs, label="标准版"):
    beijing = datetime.now(timezone(timedelta(hours=8)))
    time_str = beijing.strftime("%Y/%m/%d %H:%M")
    caption = f"""
OK影视 {label} 自动更新

本次更新：
{logs}

版本：{version}
更新时间：{time_str}
""".strip()
    with open(os.path.join(DOWNLOAD_DIR, f"caption-{label}.txt"), "w", encoding="utf-8") as f:
        f.write(caption)
    return caption

# ==== 主函数 ====
def main():
    print("==== 下载标准版 ====")
    std_ver = fetch_latest_std_version()
    std_paths = download_std(std_ver)
    std_log = parse_update_log(std_ver)
    std_caption = generate_caption(std_ver, std_log, "标准版")
    print(std_caption)

    print("\n==== 下载 Pro 版 ====")
    pro_ver = fetch_latest_pro_version()
    pro_paths = download_pro(pro_ver)
    pro_caption = generate_caption(pro_ver, "暂无更新日志", "Pro版")
    print(pro_caption)

    print("\n==== 完成 ====")
    print("标准版文件:", std_paths)
    print("Pro版文件:", pro_paths)

if __name__ == "__main__":
    main()
