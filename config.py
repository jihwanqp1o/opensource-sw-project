"""게임 설정값. 경로는 하드코딩하지 않고 환경 변수로 바꿀 수 있게 둔다."""
import os
import sys
from pathlib import Path

# 프로젝트 루트 (이 파일이 있는 폴더).
# 실행 파일(exe)로 실행하면 모델과 이미지가 풀린 폴더(sys._MEIPASS)를 쓴다.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))

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

# 사용할 마이크 번호 (python -m voice.recognizer --devices로 확인). 비우면 Windows 기본 마이크
MIC_DEVICE = os.environ.get("MIC_DEVICE", "")
MIC_DEVICE = int(MIC_DEVICE) if MIC_DEVICE.isdigit() else None

# 주문을 기다리는 시간(초). 이 시간 안에 주문이 인식되지 않으면 턴이 넘어간다 (0이면 제한 없음)
VOICE_TIMEOUT = float(os.environ.get("VOICE_TIMEOUT", "10"))

# 음성 오인식 필터: 주문 단어 신뢰도가 이 값보다 낮으면 버린다 (0이면 끔)
VOICE_MIN_CONFIDENCE = float(os.environ.get("VOICE_MIN_CONFIDENCE", "0.4"))

# 음성 오인식 필터: 주문 옆에 모르는 말([unk])이 섞여 있으면 버린다 ("0"이면 끔)
VOICE_REJECT_UNKNOWN = os.environ.get("VOICE_REJECT_UNKNOWN", "1") == "1"
