import requests
import re
import os
from datetime import datetime
from tqdm import tqdm

OK_STD_BASE = "https://op.ll.dovx.cf/OK影视/OK影视标准版"
OK_PRO_BASE = "https://op.ll.dovx.cf/OK影视/OK影视Pro"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def find_latest_version(base_url):
    print(f"扫描最新版本: {base_url}")
    major, minor = 3, 7
    latest = None

    for patch in range(0, 30):
        ver = f"{major}.{minor}.{patch}"
        url = f"{base_url}/{ver}/标准版{ver}.txt"
        r = requests.get(url)
        if r.status_code == 200 and len(r.text) > 10:
            latest = ver
        else:
            if latest:
                break

    if not latest:
        raise Exception("未找到最新版本")

    print("最新版本:", latest)
    return latest

def download_file(url, filename):
    print("下载:", filename)
    r = requests.get(url, stream=True)
    r.raise_for_status()

    path = os.path.join(DOWNLOAD_DIR, filename)
    total = int(r.headers.get("content-length", 0))

    with open(path, "wb") as f, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        desc=filename
    ) as pbar:
        for chunk in r.iter_content(8192):
            f.write(chunk)
            pbar.update(len(chunk))

def download_ok_standard():
    version = find_latest_version(OK_STD_BASE)
    base = f"{OK_STD_BASE}/{version}/"

    files = {
        f"海信专版-OK影视-{version}.apk": "hisense-tv-customized.apk",
        f"mobile-arm64_v8a-{version}.apk": "mobile-arm64_v8a-ok.apk",
        f"mobile-armeabi_v7a-{version}.apk": "mobile-arm64_v7a-ok.apk",
        f"leanback-arm64_v8a-{version}.apk": "leanback-arm64_v8a-ok.apk",
        f"leanback-armeabi_v7a-{version}.apk": "leanback-arm64_v7a-ok.apk",
        f"标准版{version}.txt": "Version-OK.txt",
    }

    for remote, local in files.items():
        try:
            download_file(base + remote, local)
        except:
            print("跳过:", remote)

def download_ok_pro():
    version = find_latest_version(OK_PRO_BASE)
    base = f"{OK_PRO_BASE}/{version}/"

    for name in [
        f"OK影视Pro-电视版-64位-{version}.apk",
        f"OK影视Pro-电视版-32位-{version}.apk",
        f"OK影视Pro-手机版-{version}.apk",
    ]:
        try:
            download_file(base + name, name)
        except:
            print("跳过:", name)

def main():
    print("开始下载 OK 标准版")
    download_ok_standard()

    print("\n开始下载 OK Pro版")
    download_ok_pro()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("\n完成时间:", ts)

if __name__ == "__main__":
    main()
