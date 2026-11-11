"""음성 인식 정확도 실험. 같은 녹음을 "단어 제한 있음/없음" 두 방식으로 인식해 비교한다.

실행: python -m voice.experiment --speaker 지환 --condition quiet
      python -m voice.experiment --wav-dir 폴더   (녹음 대신 wav 파일로, 파일 이름은 "정답__아무거나.wav")
결과는 docs/experiments/voice_results.csv에 한 줄씩 쌓인다.
"""
import argparse
import csv
import json
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


def recognize(listener, audio, samplerate, use_grammar):
    """녹음 한 개를 인식해 (인식 문장, 주문 key 또는 None, 걸린 초)를 돌려준다."""
    from vosk import KaldiRecognizer

    start = time.perf_counter()
    if use_grammar:
        rec = KaldiRecognizer(listener.model, samplerate, listener.grammar)
    else:
        rec = KaldiRecognizer(listener.model, samplerate)
    rec.AcceptWaveform(audio)
    text = json.loads(rec.FinalResult())["text"]
    return text, listener._match(text), time.perf_counter() - start


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
            with sd.RawInputStream(samplerate=rate, channels=1, dtype="int16") as stream:
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
    args = parser.parse_args()

    listener = VoiceListener(config.VOSK_MODEL_PATH, SPELLS)
    takes = read_wav_dir(args.wav_dir) if args.wav_dir else record_takes(listener, args.repeats, args.seconds)

    rows = []
    for expected, audio, rate in takes:
        for mode, use_grammar in (("grammar", True), ("free", False)):
            text, result, seconds = recognize(listener, audio, rate, use_grammar)
            correct = (result or "none") == expected
            rows.append({"time": datetime.now().isoformat(timespec="seconds"),
                         "speaker": args.speaker, "condition": args.condition,
                         "expected": expected, "mode": mode, "text": text,
                         "result": result or "none", "correct": correct,
                         "seconds": round(seconds, 3)})
            print(f"  {mode:7} 정답={expected:10} 인식={text!r:24} → {result or 'none':10} {'O' if correct else 'X'}")

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
    """방식별로 주문 정답률과 오인식률을 출력한다."""
    print("\n방식     | 주문 정답률       | 오인식률 (주문 아닌 말이 주문으로)")
    for mode in ("grammar", "free"):
        spells = [r for r in rows if r["mode"] == mode and r["expected"] != "none"]
        others = [r for r in rows if r["mode"] == mode and r["expected"] == "none"]
        hit = sum(r["correct"] for r in spells)
        wrong = sum(not r["correct"] for r in others)
        print(f"{mode:8} | {_rate(hit, len(spells)):17} | {_rate(wrong, len(others))}")


def _rate(n, total):
    return f"{n}/{total} ({n / total:.0%})" if total else "-"


if __name__ == "__main__":
    main()
