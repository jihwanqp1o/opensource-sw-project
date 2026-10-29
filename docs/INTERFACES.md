# 연결 규칙 (모듈 인터페이스)

각 모듈은 아래 함수 **이름, 인자, 반환값**을 지켜야 `main.py`에서 서로 연결됩니다.
함수 **안쪽**은 담당자가 자유롭게 고쳐도 되지만, 아래 모양을 바꾸려면 먼저 지환(@jihwanqp1o)과 상의하세요.
(이 문서를 바꾸면 `.github/copilot-instructions.md`의 요약도 같이 고칩니다.)

## 전체 흐름 (`main.py`, 담당: 지환)

```
listener.listen()            → 주문 key (예: "fireball") 또는 None
   ↓
player_turn(state, key)      → 전투 기록 문장 (state가 바뀜)
   ↓
screen.show(... banner=spell_banner(SPELLS[key].display), hit=True)
   ↓
monster_turn(state)          → 전투 기록 문장
   ↓
winner(state)                → "player" / "monster" / None  (None이면 처음으로)
```

모듈끼리 주고받는 주문 값은 항상 **주문 key 문자열**(`"fireball"`, `"shield"`, `"heal"`)입니다.

## battle — 전투 로직 (담당: 석현)

`battle/spells.py`
| 이름 | 모양 | 설명 |
|---|---|---|
| `Spell` | `key, display, kind, power, phrases` | `kind`는 `"attack"` / `"shield"` / `"heal"`, `display`는 영어 대문자, `phrases`는 음성으로 인식할 영어 말 |
| `SPELLS` | `dict[str, Spell]` | 주문 key → Spell. 다른 모듈은 이 표만 보고 주문 목록을 안다 |

`battle/engine.py`
| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `new_battle()` | → `BattleState` | 새 전투 상태 |
| `player_turn(state, spell_key)` | → `str` | 주문 효과 적용, 기록 문장 반환 |
| `monster_turn(state)` | → `str` | 몬스터 반격, 기록 문장 반환 |
| `winner(state)` | → `"player"` / `"monster"` / `None` | 승부 판정 |

`BattleState`에 반드시 있어야 하는 필드 (UI가 읽음):
`monster_name, player_hp, player_max_hp, monster_hp, monster_max_hp, shield, turn`

규칙: battle은 **화면에 출력하지 않습니다** (`print` 금지, 단독 실행 테스트 제외).

## voice — 음성 주문 인식 (담당: 지환)

`voice/recognizer.py`
| 클래스 | 만들기 | `listen()` 반환 |
|---|---|---|
| `VoiceListener` | `VoiceListener(model_path, SPELLS)` | 주문 key 또는 `None`(못 알아들음) |
| `KeyboardListener` | `KeyboardListener(SPELLS)` | 주문 key 또는 `None` |

두 클래스는 `listen()` 모양이 같아서 `main.py`는 어느 쪽인지 신경 쓰지 않습니다.

## ascii_art — 이미지·글씨 아스키 변환 (담당: 태웅)

| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `monster.image_to_ascii(path, width=40)` | → `str` (여러 줄) | 이미지 → 아스키 아트 |
| `spell_text.spell_banner(text)` | → `str` (여러 줄) | 영어 글자 → 큰 아스키 글씨 (한글 불가) |

## ui — 화면 (담당: 수빈)

`ui/screen.py`
| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `render(state, monster_art, banner=None, logs=(), hit=False, prompt="")` | → rich 렌더러블 | 화면 한 장 만들기 |
| `show(...)` | 인자는 `render`와 같음 | 화면 지우고 그리기 |

규칙: ui는 **게임 로직을 계산하지 않습니다**. 받은 `state` 값을 보여 주기만 합니다.

## 설정 (`config.py`, 담당: 지환)

경로와 숫자 설정은 여기서 가져다 씁니다. 코드 안에 경로를 직접 쓰지 않습니다.

| 이름 | 환경 변수 | 기본값 |
|---|---|---|
| `VOSK_MODEL_PATH` | `VOSK_MODEL_PATH` | `models/vosk-model-small-en-us-0.15` |
| `INPUT_MODE` | `INPUT_MODE` | `voice` (또는 `keyboard`) |
| `MONSTER_IMAGE` | `MONSTER_IMAGE` | `assets/monsters/slime.png` |
| `MONSTER_ART_WIDTH` | `MONSTER_ART_WIDTH` | `40` |
| `EFFECT_DELAY` | `EFFECT_DELAY` | `1.2` (초) |

## 모듈별 단독 실행 (내 모듈만 확인하기)

프로젝트 루트에서 실행합니다.

| 명령 | 정상이면 보이는 것 |
|---|---|
| `python -m battle.engine` | 턴별 전투 기록이 출력되고 마지막에 `승자: player` |
| `python -m ascii_art.monster` | 슬라임 모양 아스키 아트 |
| `python -m ascii_art.spell_text` | 큰 글씨 `FIREBALL` |
| `python -m ui.screen` | 가짜 값으로 그린 전투 화면 (체력바, 주문 칸, 기록 칸) |
| `python -m voice.recognizer` | 마이크에 "fireball"이라고 말하면 `인식 결과: fireball` |
