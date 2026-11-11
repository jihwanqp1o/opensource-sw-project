"""주문 입력. 마이크(Vosk)와 키보드 두 방식이 같은 listen() 모양을 가진다."""
import json
import queue


def _phrase_table(spells):
    """{"fire ball": "fireball", ...} 처럼 인식할 말 → 주문 key 표를 만든다."""
    return {phrase: spell.key for spell in spells.values() for phrase in spell.phrases}


class VoiceListener:
    """마이크로 주문을 듣는다. listen()은 주문 key를 돌려주고, 못 알아들으면 None."""

    def __init__(self, model_path, spells, min_confidence=0.0, reject_unknown=False, device=None):
        import sounddevice as sd
        from vosk import Model, SetLogLevel

        SetLogLevel(-1)  # Vosk 내부 로그 끄기
        self._sd = sd
        self.model = Model(model_path)
        self.phrases = _phrase_table(spells)
        # 인식할 단어를 주문 목록으로 제한하면 정확도가 크게 오른다
        self.grammar = json.dumps(list(self.phrases) + ["[unk]"])
        # device가 None이면 Windows 기본 마이크를 쓴다
        self.device = device
        self.samplerate = int(sd.query_devices(device, kind="input")["default_samplerate"])
        # 오인식 필터 (docs/experiments/voice-accuracy.md 참고)
        self.min_confidence = min_confidence
        self.reject_unknown = reject_unknown

    def listen(self):
        from vosk import KaldiRecognizer

        rec = KaldiRecognizer(self.model, self.samplerate, self.grammar)
        rec.SetWords(True)  # 단어별 신뢰도(conf)를 받기 위해
        audio = queue.Queue()

        def callback(indata, frames, time, status):
            audio.put(bytes(indata))

        with self._sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=self.device,
                                     dtype="int16", channels=1, callback=callback):
            while True:
                # 말이 한 번 끝날 때마다(AcceptWaveform이 True) 결과를 확인한다
                if rec.AcceptWaveform(audio.get()):
                    result = json.loads(rec.Result())
                    if result["text"]:
                        return self.decide(result)

    def decide(self, result):
        """Vosk 결과에서 주문 key를 고른다. 오인식으로 의심되면 None."""
        key = self._match(result["text"])
        words = result.get("result", [])
        if key is None or not words:
            return key
        # "hello there" → "heal [unk]"처럼 주문 옆에 모르는 말이 붙으면 오인식일 가능성이 크다
        if self.reject_unknown and any(w["word"] == "[unk]" for w in words):
            return None
        if min(w["conf"] for w in words) < self.min_confidence:
            return None
        return key

    def _match(self, text):
        # 긴 말부터 확인해서 "fire ball"이 "fire"보다 먼저 잡히게 한다
        for phrase in sorted(self.phrases, key=len, reverse=True):
            if phrase in text:
                return self.phrases[phrase]
        return None


class KeyboardListener:
    """마이크나 모델 없이 테스트할 때 쓰는 키보드 입력."""

    def __init__(self, spells):
        self.phrases = _phrase_table(spells)

    def listen(self):
        text = input("주문 입력> ").strip().lower()
        return self.phrases.get(text)


def print_input_devices():
    """마이크로 쓸 수 있는 장치 번호와 이름을 출력한다. 기본 마이크에는 * 표시."""
    import sounddevice as sd

    default = sd.default.device[0]
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            api = sd.query_hostapis(dev["hostapi"])["name"]
            print(f"{'*' if i == default else ' '} {i:3}  {dev['name']}  ({api})")


if __name__ == "__main__":
    # 단독 실행: python -m voice.recognizer            (마이크에 주문을 말해 보기, Ctrl+C로 종료)
    #           python -m voice.recognizer --devices  (마이크 번호 확인)
    import sys

    import config
    from battle.spells import SPELLS

    if "--devices" in sys.argv:
        print_input_devices()
        sys.exit()

    listener = VoiceListener(config.VOSK_MODEL_PATH, SPELLS,
                             min_confidence=config.VOICE_MIN_CONFIDENCE,
                             reject_unknown=config.VOICE_REJECT_UNKNOWN,
                             device=config.MIC_DEVICE)
    print("말해 보세요:", ", ".join(listener.phrases))
    while True:
        print("인식 결과:", listener.listen())
