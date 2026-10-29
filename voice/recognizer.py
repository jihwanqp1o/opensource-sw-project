"""주문 입력. 마이크(Vosk)와 키보드 두 방식이 같은 listen() 모양을 가진다."""
import json
import queue


def _phrase_table(spells):
    """{"fire ball": "fireball", ...} 처럼 인식할 말 → 주문 key 표를 만든다."""
    return {phrase: spell.key for spell in spells.values() for phrase in spell.phrases}


class VoiceListener:
    """마이크로 주문을 듣는다. listen()은 주문 key를 돌려주고, 못 알아들으면 None."""

    def __init__(self, model_path, spells):
        import sounddevice as sd
        from vosk import Model, SetLogLevel

        SetLogLevel(-1)  # Vosk 내부 로그 끄기
        self._sd = sd
        self.model = Model(model_path)
        self.phrases = _phrase_table(spells)
        # 인식할 단어를 주문 목록으로 제한하면 정확도가 크게 오른다
        self.grammar = json.dumps(list(self.phrases) + ["[unk]"])
        self.samplerate = int(sd.query_devices(kind="input")["default_samplerate"])

    def listen(self):
        from vosk import KaldiRecognizer

        rec = KaldiRecognizer(self.model, self.samplerate, self.grammar)
        audio = queue.Queue()

        def callback(indata, frames, time, status):
            audio.put(bytes(indata))

        with self._sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                                     dtype="int16", channels=1, callback=callback):
            while True:
                # 말이 한 번 끝날 때마다(AcceptWaveform이 True) 결과를 확인한다
                if rec.AcceptWaveform(audio.get()):
                    text = json.loads(rec.Result())["text"]
                    if text:
                        return self._match(text)

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


if __name__ == "__main__":
    # 단독 실행: python -m voice.recognizer  (마이크에 주문을 말해 보기, Ctrl+C로 종료)
    import config
    from battle.spells import SPELLS

    listener = VoiceListener(config.VOSK_MODEL_PATH, SPELLS)
    print("말해 보세요:", ", ".join(listener.phrases))
    while True:
        print("인식 결과:", listener.listen())
