"""음성 인식 정확도 실험. 같은 녹음을 세 방식으로 인식해 비교한다.

- grammar: 단어를 주문 목록으로 제한
- filtered: grammar + 오인식 필터 (게임에서 실제로 쓰는 방식, 기준값은 config.py)
- free: 제한 없이 자유 인식

실행: python -m voice.experiment --speaker 지환 --condition quiet
      python -m voice.experiment --wav-dir 폴더   (녹음 대신 wav 파일로, 파일 이름은 "정답__아무거나.wav")
      python -m voice.experiment --wav-dir 폴더 --degrade   (뭉개진 발음·나쁜 환경 변형까지 함께)
결과는 docs/experiments/voice_results.csv에 한 줄씩 쌓인다.
"""
import argparse
import array
import csv
import json
import math
import random
import time
import wave
from datetime import datetime
from pathlib import Path

import config
from battle.spells import SPELLS
from voice.recognizer import VoiceListener

RESULT_CSV = config.ROOT / "docs" / "experiments" / "voice_results.csv"
FIELDS = ["time", "speaker", "condition", "expected", "mode", "text", "result", "correct", "seconds"]

# 주문이 아닌 말: 주문으로 잘못 잡히는지(오인식) 확인용
NON_SPELLS = ["hello there", "what time is it", "아무 한국어 문장"]


MODES = ("grammar", "filtered", "free")

# 깨끗한 녹음(특히 TTS)을 일부러 망가뜨려 실제 발표장과 비슷한 나쁜 조건을 흉내 낸다
DEGRADES = {
    "noise10": "잡음 섞임 (신호 대 잡음 10dB, 웅성거리는 교실)",
    "noise5": "큰 잡음 (5dB, 시끄러운 발표장)",
    "muffled": "뭉개진 발음, 웅얼거림, 성능 낮은 마이크 (고음 깎임)",
    "quiet": "작게 말하거나 마이크에서 멂 (소리 15%)",
    "fast": "빠르게 말해 발음이 뭉개짐 (1.35배속)",
    "cut": "말끝 흐림 (말소리 뒷부분 30% 잘림)",
    "mixed": "웅얼거림 + 빠르게 + 잡음 10dB (가장 나쁜 경우)",
}


def degrade(audio, rate, kind, seed=0):
    """16비트 녹음(bytes)을 kind에 맞게 망가뜨려 돌려준다. numpy 없이 표준 라이브러리만 쓴다."""
    if kind == "mixed":
        for step in ("muffled", "fast", "noise10"):
            audio = degrade(audio, rate, step, seed)
        return audio

    s = array.array("h")
    s.frombytes(audio)
    voiced = [x for x in s if abs(x) > 500] or [1]  # 말소리 부분 (조용한 앞뒤는 뺀다)

    if kind.startswith("noise"):
        snr_db = int(kind[len("noise"):])
        speech_power = sum(x * x for x in voiced) / len(voiced)
        std = math.sqrt(speech_power / 10 ** (snr_db / 10))
        rnd = random.Random(seed)
        out = [x + rnd.gauss(0, std) for x in s]
    elif kind == "muffled":
        window = max(2, rate // 2000)  # 이동 평균으로 2kHz 위쪽 소리를 깎는다
        total, out = 0, []
        for i, x in enumerate(s):
            total += x - (s[i - window] if i >= window else 0)
            out.append(total / window)
    elif kind == "quiet":
        out = [x * 0.15 for x in s]
    elif kind == "fast":
        out = [s[int(i * 1.35)] for i in range(int(len(s) / 1.35))]
    elif kind == "cut":
        idx = [i for i, x in enumerate(s) if abs(x) > 500] or [0]
        end = idx[0] + int((idx[-1] - idx[0]) * 0.7)
        out = list(s[:end]) + [0] * (rate // 2)
    else:
        raise ValueError(f"알 수 없는 변형: {kind}")
    return array.array("h", (max(-32768, min(32767, int(x))) for x in out)).tobytes()


def recognize(listener, audio, samplerate, mode):
    """녹음 한 개를 인식해 (인식 문장, 주문 key 또는 None, 걸린 초)를 돌려준다."""
    from vosk import KaldiRecognizer

    start = time.perf_counter()
    if mode == "free":
        rec = KaldiRecognizer(listener.model, samplerate)
    else:
        rec = KaldiRecognizer(listener.model, samplerate, listener.grammar)
    rec.SetWords(True)
    rec.AcceptWaveform(audio)
    result = json.loads(rec.FinalResult())
    key = listener.decide(result) if mode == "filtered" else listener._match(result["text"])
    return result["text"], key, time.perf_counter() - start


def record_takes(listener, repeats, seconds):
    """화면 안내에 따라 녹음한다. (정답, 녹음 bytes, 샘플레이트)를 하나씩 돌려준다."""
    sd = listener._sd
    rate = listener.samplerate
    prompts = [(key, SPELLS[key].phrases[0]) for key in SPELLS] + [("none", s) for s in NON_SPELLS]
    for expected, say in prompts:
        for i in range(repeats):
            input(f'[{i + 1}/{repeats}] "{say}" 라고 말할 준비가 되면 Enter > ')
            print(f"  녹음 중... ({seconds}초)")
            # sd.rec는 numpy가 필요해서, 게임과 같은 RawInputStream으로 녹음한다
            with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16",
                                   device=listener.device) as stream:
                audio, _ = stream.read(int(seconds * rate))
            yield expected, bytes(audio), rate


def read_wav_dir(folder):
    """wav 파일을 읽는다. 파일 이름 "fireball__david.wav"에서 "__" 앞이 정답이다."""
    for path in sorted(Path(folder).glob("*.wav")):
        with wave.open(str(path), "rb") as wf:
            yield path.stem.split("__")[0], wf.readframes(wf.getnframes()), wf.getframerate()


def main():
    parser = argparse.ArgumentParser(description="음성 인식 정확도 실험")
    parser.add_argument("--speaker", default="unknown", help="말한 사람 이름")
    parser.add_argument("--condition", default="quiet", help="환경 (예: quiet, noisy, korean-accent)")
    parser.add_argument("--repeats", type=int, default=3, help="말마다 반복 횟수")
    parser.add_argument("--seconds", type=float, default=2.5, help="한 번 녹음 길이(초)")
    parser.add_argument("--wav-dir", help="녹음 대신 이 폴더의 wav 파일로 실험")
    parser.add_argument("--degrade", action="store_true",
                        help="원래 녹음과 함께 뭉개진 발음·잡음 등 나쁜 조건 변형으로도 실험")
    args = parser.parse_args()

    listener = VoiceListener(config.VOSK_MODEL_PATH, SPELLS,
                             min_confidence=config.VOICE_MIN_CONFIDENCE,
                             reject_unknown=config.VOICE_REJECT_UNKNOWN,
                             device=config.MIC_DEVICE)
    takes = read_wav_dir(args.wav_dir) if args.wav_dir else record_takes(listener, args.repeats, args.seconds)

    rows = []
    variants = ["original"] + (list(DEGRADES) if args.degrade else [])
    for expected, audio, rate in takes:
        for variant in variants:
            sample = audio if variant == "original" else degrade(audio, rate, variant)
            condition = args.condition if variant == "original" else f"{args.condition}+{variant}"
            for mode in MODES:
                text, result, seconds = recognize(listener, sample, rate, mode)
                correct = (result or "none") == expected
                rows.append({"time": datetime.now().isoformat(timespec="seconds"),
                             "speaker": args.speaker, "condition": condition,
                             "expected": expected, "mode": mode, "text": text,
                             "result": result or "none", "correct": correct,
                             "seconds": round(seconds, 3)})
                if not args.degrade:
                    print(f"  {mode:7} 정답={expected:10} 인식={text!r:24} → {result or 'none':10} "
                          f"{'O' if correct else 'X'}")

    RESULT_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_file = not RESULT_CSV.exists()
    with open(RESULT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)

    print_summary(rows)
    print(f"\n결과 저장: {RESULT_CSV}")


def print_summary(rows):
    """조건(변형)별, 방식별로 주문 정답률, 오인식률, 다른 주문으로 잘못 잡힌 횟수를 출력한다."""
    for condition in dict.fromkeys(r["condition"] for r in rows):
        print(f"\n[{condition}]")
        print("방식     | 주문 정답률       | 다른 주문으로 | 오인식률 (주문 아닌 말이 주문으로)")
        for mode in MODES:
            group = [r for r in rows if r["condition"] == condition and r["mode"] == mode]
            spells = [r for r in group if r["expected"] != "none"]
            others = [r for r in group if r["expected"] == "none"]
            hit = sum(r["correct"] for r in spells)
            # 가장 위험한 경우: 말한 것과 다른 주문이 발동
            confused = sum(r["result"] not in ("none", r["expected"]) for r in spells)
            wrong = sum(not r["correct"] for r in others)
            print(f"{mode:8} | {_rate(hit, len(spells)):17} | {confused:13} | {_rate(wrong, len(others))}")


def _rate(n, total):
    return f"{n}/{total} ({n / total:.0%})" if total else "-"


if __name__ == "__main__":
    main()
