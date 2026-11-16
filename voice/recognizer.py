"""주문 입력. 마이크(Vosk)와 키보드 두 방식이 같은 listen() 모양을 가진다."""
import json
import queue
import time


def _phrase_table(spells):
    """{"fire ball": "fireball", ...} 처럼 인식할 말 → 주문 key 표를 만든다."""
    return {phrase: spell.key for spell in spells.values() for phrase in spell.phrases}


class VoiceListener:
    """마이크로 주문을 듣는다. listen()은 주문 key를 돌려주고, 못 알아들으면 None."""

    def __init__(self, model_path, spells, min_confidence=0.0, reject_unknown=False, device=None,
                 timeout=None, on_status=None):
        import sounddevice as sd
        from vosk import Model, SetLogLevel

        SetLogLevel(-1)  # Vosk 내부 로그 끄기
        self._sd = sd
        self.model = Model(model_path)
        self.phrases = _phrase_table(spells)
        # 인식할 단어를 주문 목록으로 제한하면 정확도가 크게 오른다
        self.grammar = json.dumps(list(self.phrases) + ["[unk]"])
        self._active = self.phrases  # 지금 듣는 말 → key 표 (listen(choices)로 잠깐 바뀜)
        self._choices_mode = False   # 방향처럼 고를 것이 적을 때는 [unk] 필터를 끈다 (아래 decide 참고)
        # device가 None이면 Windows 기본 마이크를 쓴다
        self.device = device
        self.samplerate = int(sd.query_devices(device, kind="input")["default_samplerate"])
        # 오인식 필터 (docs/experiments/voice-accuracy.md 참고)
        self.min_confidence = min_confidence
        self.reject_unknown = reject_unknown
        # timeout초 안에 주문이 인식되지 않으면 None (None이나 0이면 시간 제한 없음)
        self.timeout = timeout
        # 듣는 동안 on_status(지금까지 들린 말, 남은 초)를 계속 불러 준다 (화면 표시용)
        self.on_status = on_status
        # 마지막 listen()이 어떻게 입력받았는지: "voice" 또는 "keyboard"(비상 키보드 입력)
        self.last_source = "voice"
        self._typed = ""

    def listen(self, choices=None):
        """주문 key를 돌려준다. choices({말: key}, 예: 갈림길 방향)를 주면 그 말만 듣고 그 key를 돌려준다."""
        from vosk import KaldiRecognizer

        self._active = choices or self.phrases
        self._choices_mode = bool(choices)
        grammar = json.dumps(list(choices) + ["[unk]"]) if choices else self.grammar
        rec = KaldiRecognizer(self.model, self.samplerate, grammar)
        rec.SetWords(True)  # 단어별 신뢰도(conf)를 받기 위해
        audio = queue.Queue()
        deadline = time.monotonic() + self.timeout if self.timeout else None
        heard = ""  # 화면에 보여 줄 "지금까지 들린 말"
        self.last_source = "voice"
        self._typed = ""  # 비상 키보드 입력 중인 글자

        def callback(indata, frames, time_info, status):
            audio.put(bytes(indata))

        with self._sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=self.device,
                                     dtype="int16", channels=1, callback=callback):
            while True:
                remaining = deadline - time.monotonic() if deadline else None
                if remaining is not None and remaining <= 0:
                    # 시간이 다 되면 말하던 중인 것까지 확인하고 끝낸다
                    result = json.loads(rec.FinalResult())
                    return self.decide(result) if result["text"] else None

                # 발표장 소음 등으로 음성이 안 될 때를 대비해, 듣는 중에도 키보드 입력을 받는다
                typed_key = self._poll_keyboard()
                if typed_key:
                    self.last_source = "keyboard"
                    return typed_key

                try:
                    data = audio.get(timeout=0.2)
                except queue.Empty:
                    data = None

                # 말이 한 번 끝날 때마다(AcceptWaveform이 True) 결과를 확인한다
                if data is None:
                    pass
                elif rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    key = self.decide(result) if result["text"] else None
                    if key:
                        return key
                    # 기침, 잡음, 주문이 아닌 말은 무시하고 시간 안에서 계속 듣는다
                    if result["text"]:
                        heard = "(다시 말해 주세요)"
                else:
                    partial = json.loads(rec.PartialResult())["partial"]
                    if partial:
                        heard = partial.replace("[unk]", "...")  # 모르는 말은 ...로 보여 준다
                if self.on_status:
                    self.on_status(f"키보드: {self._typed}" if self._typed else heard, remaining)

    def _poll_keyboard(self):
        """눌린 키를 모아 두었다가 Enter를 누르면 주문 key를 돌려준다. 키 입력이 없으면 None. (Windows 전용)"""
        try:
            import msvcrt
        except ImportError:
            return None
        while msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                text, self._typed = self._typed.strip().lower(), ""
                if text in self._active:
                    return self._active[text]
            elif ch == "\b":
                self._typed = self._typed[:-1]
            elif ch in ("\x00", "\xe0"):
                msvcrt.getwch()  # 방향키 같은 특수 키는 두 글자로 들어와서 함께 버린다
            elif ch.isprintable():
                self._typed += ch
        return None

    def decide(self, result):
        """Vosk 결과에서 주문 key를 고른다. 오인식으로 의심되면 None."""
        key = self._match(result["text"])
        words = result.get("result", [])
        if key is None or not words:
            return key
        # "hello there" → "heal [unk]"처럼 주문 옆에 모르는 말이 붙으면 오인식일 가능성이 크다.
        # 방향(choices)은 고를 것이 2~3개뿐이고, 한국식 발음 "레프트"가 "left [unk]"로 들려서 이 필터를 쓰지 않는다
        if self.reject_unknown and not self._choices_mode and any(w["word"] == "[unk]" for w in words):
            return None
        if min(w["conf"] for w in words) < self.min_confidence:
            return None
        return key

    def _match(self, text):
        # 긴 말부터 확인해서 "fire ball"이 "fire"보다 먼저 잡히게 한다
        for phrase in sorted(self._active, key=len, reverse=True):
            if phrase in text:
                return self._active[phrase]
        return None


class KeyboardListener:
    """마이크나 모델 없이 테스트할 때 쓰는 키보드 입력."""

    def __init__(self, spells):
        self.phrases = _phrase_table(spells)

    def listen(self, choices=None):
        text = input("방향 입력> " if choices else "주문 입력> ").strip().lower()
        return (choices or self.phrases).get(text)


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
                             device=config.MIC_DEVICE,
                             timeout=config.VOICE_TIMEOUT,
                             on_status=lambda heard, left: print(
                                 f"\r  듣는 중... {left or 0:4.1f}초 | {heard}".ljust(60), end=""))
    print("말해 보세요:", ", ".join(listener.phrases))
    while True:
        key = listener.listen()
        print("\n인식 결과:", key if key else "None (시간 초과)")
