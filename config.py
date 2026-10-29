"""게임 설정값. 경로는 하드코딩하지 않고 환경 변수로 바꿀 수 있게 둔다."""
import os
from pathlib import Path

# 프로젝트 루트 (이 파일이 있는 폴더)
ROOT = Path(__file__).resolve().parent

# Vosk 모델 폴더. 환경 변수 VOSK_MODEL_PATH가 있으면 그 값을 쓴다.
VOSK_MODEL_PATH = os.environ.get(
    "VOSK_MODEL_PATH", str(ROOT / "models" / "vosk-model-small-en-us-0.15")
)

# 입력 방식: "voice"(마이크) 또는 "keyboard"(마이크·모델 없이 테스트할 때)
INPUT_MODE = os.environ.get("INPUT_MODE", "voice")

# 몬스터 이미지 경로
MONSTER_IMAGE = os.environ.get(
    "MONSTER_IMAGE", str(ROOT / "assets" / "monsters" / "slime.png")
)

# 몬스터 아스키 아트 가로 글자 수
MONSTER_ART_WIDTH = int(os.environ.get("MONSTER_ART_WIDTH", "40"))

# 연출 사이 대기 시간(초)
EFFECT_DELAY = float(os.environ.get("EFFECT_DELAY", "1.2"))
