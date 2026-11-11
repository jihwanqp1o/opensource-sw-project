"""시연용 배포 파일을 만든다. (Windows 전용)

실행: pip install -r requirements-dev.txt
      python packaging/build.py
결과: dist/release/VoiceShell.zip   휴대용 폴더 (기본). 압축을 풀고 VoiceShell.bat 더블클릭
      dist/release/VoiceShell.exe   파일 하나 (빠른 실행용). 스마트 앱 컨트롤이 켜진 PC에서는 막힐 수 있다

zip은 python.org의 서명된 공식 휴대용 Python으로 게임을 실행한다. 서명되지 않은 exe가 없어서
Windows 스마트 앱 컨트롤이 켜진 PC에서도 막히지 않는다. (README의 "바로 플레이하기" 참고)
"""
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "VoiceShell"
MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
MODEL_DIR = ROOT / "models" / MODEL_NAME
# python.org는 3.12.10까지만 휴대용(embeddable) Python을 배포한다
EMBED_VERSION = "3.12.10"
EMBED_URL = f"https://www.python.org/ftp/python/{EMBED_VERSION}/python-{EMBED_VERSION}-embed-amd64.zip"
GAME_FILES = ["main.py", "config.py", "battle", "voice", "ascii_art", "ui", "assets"]
DIST = ROOT / "dist"
WORK = ROOT / "build"
GUIDE = Path(__file__).resolve().parent / "READ_ME.txt"

LAUNCHER = """@echo off
title VOICE SHELL
cd /d "%~dp0game"
"%~dp0python\\python.exe" main.py %*
if errorlevel 1 pause
"""


def download(url, dest):
    print(f"내려받는 중: {url}")
    WORK.mkdir(exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def ensure_model():
    """모델이 없으면 내려받는다 (CI에서는 항상 내려받게 된다)."""
    if MODEL_DIR.exists():
        return
    zip_path = WORK / f"{MODEL_NAME}.zip"
    download(MODEL_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(MODEL_DIR.parent)


def build_portable(release):
    """휴대용 폴더: python/ (공식 Python + 라이브러리), game/ (코드, 이미지, 모델), VoiceShell.bat"""
    folder = DIST / "portable" / NAME
    shutil.rmtree(folder.parent, ignore_errors=True)
    python_dir = folder / "python"
    game_dir = folder / "game"

    embed_zip = WORK / f"python-{EMBED_VERSION}-embed-amd64.zip"
    if not embed_zip.exists():
        download(EMBED_URL, embed_zip)
    with zipfile.ZipFile(embed_zip) as zf:
        zf.extractall(python_dir)

    # 라이브러리는 휴대용 Python 안의 Lib/site-packages에 설치한다
    site_packages = python_dir / "Lib" / "site-packages"
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--target", str(site_packages),
                    "-r", str(ROOT / "requirements.txt")], check=True)
    # 휴대용 Python이 라이브러리와 게임 코드를 찾을 수 있게 경로를 알려 준다
    (python_dir / "python312._pth").write_text(
        "python312.zip\n.\nLib\\site-packages\n..\\game\nimport site\n", encoding="utf-8")

    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for name in GAME_FILES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, game_dir / name, ignore=ignore)
        else:
            game_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, game_dir / name)
    shutil.copytree(MODEL_DIR, game_dir / "models" / MODEL_NAME)

    (folder / f"{NAME}.bat").write_text(LAUNCHER, encoding="ascii", newline="\r\n")
    shutil.copy(GUIDE, folder / GUIDE.name)
    shutil.make_archive(str(release / NAME), "zip", folder.parent, NAME)


def build_exe(release):
    """PyInstaller로 파일 하나짜리 exe를 만든다. 모델과 이미지는 exe 안에 함께 넣는다."""
    sep = os.pathsep
    subprocess.run([
        sys.executable, "-m", "PyInstaller", str(ROOT / "main.py"),
        "--onefile", "--name", NAME, "--console", "--noconfirm", "--log-level", "WARN",
        # vosk의 dll, 마이크용 portaudio dll, pyfiglet 글꼴은 자동으로 안 따라와서 직접 지정한다
        "--collect-all", "vosk",
        "--collect-data", "_sounddevice_data",
        "--collect-data", "pyfiglet",
        "--add-data", f"{ROOT / 'assets'}{sep}assets",
        "--add-data", f"{MODEL_DIR}{sep}models/{MODEL_NAME}",
        "--distpath", str(DIST / "onefile"),
        "--workpath", str(WORK / "onefile"),
        "--specpath", str(WORK),
    ], check=True, cwd=ROOT)
    shutil.copy(DIST / "onefile" / f"{NAME}.exe", release / f"{NAME}.exe")


def main():
    ensure_model()
    release = DIST / "release"
    shutil.rmtree(release, ignore_errors=True)
    release.mkdir(parents=True)

    print("1/2 휴대용 zip 만드는 중")
    build_portable(release)
    print("2/2 파일 하나짜리 exe 만드는 중")
    build_exe(release)

    for f in sorted(release.iterdir()):
        print(f"완성: {f}  ({f.stat().st_size / 1024 / 1024:.0f}MB)")


if __name__ == "__main__":
    main()
