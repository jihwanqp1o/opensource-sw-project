# 연결 규칙 (모듈 인터페이스)

각 모듈은 아래 함수 **이름, 인자, 반환값**을 지켜야 `main.py`에서 서로 연결됩니다.
함수 **안쪽**은 담당자가 자유롭게 고쳐도 되지만, 아래 모양을 바꾸려면 먼저 지환(@jihwanqp1o)과 상의하세요.
(이 문서를 바꾸면 `.github/copilot-instructions.md`의 요약도 같이 고칩니다.)

## 전체 흐름 (`main.py`, 담당: 지환)

```
listener.listen()            → 주문 key (예: "fireball") 또는 None
   ↓
player_turn(state, key)      → 전투 기록 문장 (state가 바뀜, key가 None이면 턴 넘김)
   ↓
screen.show(... banner=spell_banner(SPELLS[key].display), hit=True)
   ↓
(state.awaiting_upgrade가 True면) 업그레이드 화면 → apply_upgrade(state, "1"|"2"|"3") → 다음 스테이지로, 처음으로
   ↓
monster_turn(state)          → 전투 기록 문장
   ↓
winner(state)                → "player"(마지막 스테이지 처치) / "monster" / None  (None이면 처음으로)
```

모듈끼리 주고받는 주문 값은 항상 **주문 key 문자열**(`"fireball"`, `"lightning"`, `"shield"`, `"heal"`)입니다. 주문 목록은 `battle/spells.py`의 `SPELLS`가 기준이며, 다른 모듈은 key를 직접 나열하지 말고 `SPELLS`에서 읽습니다.

## battle — 전투 로직 (담당: 석현)

`battle/spells.py`
| 이름 | 모양 | 설명 |
|---|---|---|
| `Spell` | `key, display, kind, power, phrases, mana_cost, starter, desc` | `kind`는 `"attack"` / `"shield"` / `"heal"` / `"freeze"` / `"mana"` / `"drain"`, `display`는 영어 대문자, `phrases`는 음성으로 인식할 영어 말, `starter=False`면 상점에서 배워야 함 |
| `SPELLS` | `dict[str, Spell]` | 주문 key → Spell. 다른 모듈은 이 표만 보고 주문 목록을 안다 |

`battle/engine.py`
| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `STAGES` | `dict[int, (이름, 체력, 기본 공격, 강화 공격)]` | 4연전 몬스터 표. 이름은 docs/CONCEPT.md를 따름 |
| `new_battle(monster_hp_rate=1.0)` | → `BattleState` | 1스테이지부터 시작하는 새 전투 상태. `monster_hp_rate`로 모든 몬스터 체력을 줄임 (시연 모드 0.4) |
| `player_turn(state, spell_key)` | → `str` | 주문 효과 적용, 기록 문장 반환. `spell_key`가 `None`이거나 없는 주문이면 턴을 넘기는 문장 반환. 중간 스테이지 몬스터를 쓰러뜨리면 `state.awaiting_upgrade = True` |
| `monster_turn(state)` | → `str` | 몬스터 반격, 기록 문장 반환 |
| `get_shop_options(state)` | → `list[(번호, 설명)]` | 상점 선택지. `"1"`~`"3"` 스탯 강화, `"4"`~`"7"` 아직 안 배운 주문 (번호 고정: `SHOP_SPELL_NUMBERS`) |
| `apply_upgrade(state, choice)` | → `str` | 스탯 강화 또는 주문 설치(번호나 주문 이름) 후 다음 스테이지로. 없는 선택·이미 배운 주문이면 `ValueError` |
| `get_upgrade_prompt()` | → `str` | 스탯 강화 선택지 문장 (예전 방식, 주문까지 보려면 `get_shop_options`) |
| `winner(state)` | → `"player"` / `"monster"` / `None` | 승부 판정. 상태를 바꾸지 않음. 마지막 스테이지를 깨야 `"player"` |

`BattleState`에 반드시 있어야 하는 필드 (UI가 읽음):
`monster_name, player_hp, player_max_hp, player_mp, player_max_mp, monster_hp, monster_max_hp, shield, turn, stage, awaiting_upgrade, bonus_attack, bonus_heal, bonus_crit, known_spells, monster_frozen`

마나 규칙: 주문을 쓰면 `mana_cost`만큼 줄고, 몬스터 턴마다 `MP_REGEN`(10) 회복. 모자라거나 안 배운 주문이면 `player_turn`이 `[FAIL]` 문장을 돌려주고 턴이 넘어감.

규칙: battle은 **화면에 출력하지 않습니다** (`print` 금지, 단독 실행 테스트 제외).

## voice — 음성 주문 인식 (담당: 지환)

`voice/recognizer.py`
| 클래스 | 만들기 | `listen()` 반환 |
|---|---|---|
| `VoiceListener` | `VoiceListener(model_path, SPELLS, min_confidence=0.0, reject_unknown=False, device=None, timeout=None, on_status=None)` | 주문 key, 또는 `timeout`초 안에 주문이 인식되지 않으면 `None`. 듣는 중에 키보드로 주문을 치고 Enter를 눌러도 발동(비상 입력, Windows). 어떻게 입력됐는지는 `listener.last_source`(`"voice"` / `"keyboard"`) |

`on_status(heard, remaining)`: 듣는 동안 약 0.2초마다 불립니다. `heard`는 지금까지 들린 말, `remaining`은 남은 초(시간 제한이 없으면 `None`)입니다. 화면에 듣는 중 상태를 보여 줄 때 씁니다.
| `KeyboardListener` | `KeyboardListener(SPELLS)` | 주문 key 또는 `None` |

두 클래스는 `listen()` 모양이 같아서 `main.py`는 어느 쪽인지 신경 쓰지 않습니다.

## ascii_art — 이미지·글씨 아스키 변환 (담당: 태웅)

| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `monster.image_to_ascii(path, width=40)` | → `str` (여러 줄) | 이미지 → 아스키 아트 |
| `spell_text.spell_banner(text)` | → `str` (여러 줄) | 영어 글자 → 큰 아스키 글씨 (한글 불가) |
| `intro.boot_lines()` | → `list[(str, float)]` | 부팅 오프닝 (한 줄, 그 줄 뒤에 기다릴 초). 글자에 rich 색 표시 가능. 화면에 찍는 건 main.py |

## ui — 화면 (담당: 수빈)

`ui/screen.py`
| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `render(state, monster_art, banner=None, logs=(), hit=False, prompt="")` | → rich 렌더러블 | 화면 한 장 만들기 |
| `show(...)` | 인자는 `render`와 같음 | 화면 지우고 그리기 |

`ui/menu.py` (전투 밖 화면, 플레이 모드용)
| 함수 | 인자 → 반환 | 설명 |
|---|---|---|
| `title_screen(demo=False)` | → rich 렌더러블 | 타이틀(메인) 화면과 메뉴 안내. `demo=True`면 `DEMO` 표시 |
| `spell_list_screen(SPELLS)` | → rich 렌더러블 | 주문 목록 |
| `upgrade_screen(state, options, total_stages)` | → rich 렌더러블 | 스테이지를 깬 뒤 상점(패키지 저장소) 화면. `options`는 `get_shop_options(state)` |
| `result_screen(won, stats)` | → rich 렌더러블 | 결과 화면. `stats`: `seconds`, `turns`, `spells`(Counter), `recognized`, `missed`, `stage`(예: `"3/4"`) |
| `test_banner(state, input_mode)` | → rich 렌더러블 | 테스트 모드 화면 맨 위에 붙는 노란 줄 |

플레이 모드와 테스트 모드 흐름은 `main.py`가 정하고, ui는 화면만 만듭니다.

규칙: ui는 **게임 로직을 계산하지 않습니다**. 받은 `state` 값을 보여 주기만 합니다.

## 설정 (`config.py`, 담당: 지환)

경로와 숫자 설정은 여기서 가져다 씁니다. 코드 안에 경로를 직접 쓰지 않습니다.

| 이름 | 환경 변수 | 기본값 |
|---|---|---|
| `VOSK_MODEL_PATH` | `VOSK_MODEL_PATH` | `models/vosk-model-small-en-us-0.15` |
| `INPUT_MODE` | `INPUT_MODE` | `voice` (또는 `keyboard`) |
| `MONSTER_IMAGE` | `MONSTER_IMAGE` | `assets/monsters/slime.png` (스테이지 그림이 없을 때 대신 쓰는 기본 그림) |
| `MONSTER_IMAGE_DIR` | `MONSTER_IMAGE_DIR` | `assets/monsters` |
| `STAGE_MONSTER_IMAGES` | - | `{1: slime.png, 2: goblin.png, 3: zombie.png, 4: dragon.png}`. 이 이름으로 그림 파일을 `assets/monsters/`에 넣으면 그 스테이지에 바로 나옵니다 |
| `MONSTER_ART_WIDTH` | `MONSTER_ART_WIDTH` | `40` |
| `EFFECT_DELAY` | `EFFECT_DELAY` | `1.2` (초) |
| `DEMO_HP_RATE` | `DEMO_HP_RATE` | `0.4` (`--demo`일 때 몬스터 체력 배율) |
| `VOICE_MIN_CONFIDENCE` | `VOICE_MIN_CONFIDENCE` | `0.4` (이보다 낮은 신뢰도는 버림, 0이면 끔) |
| `VOICE_REJECT_UNKNOWN` | `VOICE_REJECT_UNKNOWN` | `1` (주문 옆에 모르는 말이 섞이면 버림, `0`이면 끔) |
| `VOICE_TIMEOUT` | `VOICE_TIMEOUT` | `10` (초, 이 안에 주문이 인식되지 않으면 턴 넘김, 0이면 제한 없음) |
| `MIC_DEVICE` | `MIC_DEVICE` | 비어 있음 (Windows 기본 마이크). 번호는 `python -m voice.recognizer --devices`로 확인 |

## 모듈별 단독 실행 (내 모듈만 확인하기)

프로젝트 루트에서 실행합니다.

| 명령 | 정상이면 보이는 것 |
|---|---|
| `python -m battle.engine` | 턴별 전투 기록이 출력되고 마지막에 `승자: player` |
| `python -m ascii_art.monster` | 슬라임 모양 아스키 아트 |
| `python -m ascii_art.spell_text` | 큰 글씨 `FIREBALL` |
| `python -m ascii_art.intro` | 부팅 오프닝이 한 줄씩 찍힘 |
| `python -m ui.screen` | 가짜 값으로 그린 전투 화면 (체력바, 주문 칸, 기록 칸) |
| `python -m ui.menu` | 타이틀, 주문 목록, 결과 화면, TEST MODE 줄 |
| `python -m voice.recognizer` | 마이크에 "fireball"이라고 말하면 `인식 결과: fireball` |
| `python -m voice.recognizer --devices` | 마이크 번호와 이름 목록 (`*`가 기본 마이크) |
