# Copilot 작업 규칙 (마법 음성 전투 게임)

이 저장소는 오픈소스SW 팀 프로젝트로, 마이크에 영어 주문을 말하면 Vosk로 인식해 몬스터와 턴제로 싸우는 Python 터미널 게임이다.
팀원 대부분이 AI 코딩이 처음이므로, 답변은 한국어로 쉽게 설명한다.

## 반드시 지킬 것

1. **요청받은 기능 하나만** 고친다. 요청하지 않은 파일을 새로 만들거나, 옮기거나, 이름을 바꾸지 않는다.
   - 폴더·파일 구조 변경은 지환(@jihwanqp1o) 담당이다. 구조 변경이 필요해 보이면 직접 바꾸지 말고 "지환과 상의하세요"라고 안내한다.
2. **담당 모듈 밖의 파일은 고치지 않는다.** 다른 모듈 수정이 필요하면 그 담당자에게 요청하라고 안내한다.
   - `voice/`, `main.py`, `config.py`: 지환 / `battle/`: 석현 / `ascii_art/`: 태웅 / `ui/`: 수빈
3. **연결 규칙(아래 함수 이름·인자·반환값)을 바꾸지 않는다.** 함수 안쪽만 고친다. 자세한 내용은 `docs/INTERFACES.md`.
4. 기존 코드의 이름 규칙, 주석 밀도(짧은 한국어 주석), 들여쓰기(공백 4칸)를 따른다.
5. 경로나 설정 숫자를 코드에 직접 쓰지 않는다. `config.py`의 값을 쓰거나 거기에 추가하도록 안내한다.
6. Vosk 모델(`models/`), `venv/`, `.env`, API 키는 저장소에 넣지 않는다.
7. 코드를 줄 때는 **실행 명령**과 **정상이면 화면에 무엇이 보이는지**를 함께 알려 준다.
   - 모듈 단독 확인: `python -m battle.engine`, `python -m ascii_art.monster`, `python -m ascii_art.spell_text`, `python -m ui.screen`, `python -m voice.recognizer`
   - 게임 전체: `python main.py --keyboard` (마이크 없이), `python main.py` (마이크)
8. 커밋 메시지는 접두사를 붙인다: `feat:` 새 기능, `fix:` 버그 수정, `docs:` 문서, `refactor:` 구조 변경. 예: `fix: 주문 이름 대소문자 인식 오류 수정`
9. `main`에 직접 push하지 않는다. `feature/기능이름` 브랜치에서 작업하고 PR을 올린다.

## 연결 규칙 요약

- 모듈끼리 주고받는 주문 값은 주문 key 문자열 (`"fireball"`, `"shield"`, `"heal"`)
- `battle.spells.SPELLS: dict[str, Spell]` / `Spell(key, display, kind, power, phrases)`
- `battle.engine`: `new_battle() -> BattleState`, `player_turn(state, spell_key) -> str`, `monster_turn(state) -> str`, `winner(state) -> "player" | "monster" | None`
  - `BattleState` 필수 필드: `monster_name, player_hp, player_max_hp, monster_hp, monster_max_hp, shield, turn`
  - battle은 print하지 않는다
- `voice.recognizer`: `VoiceListener(model_path, SPELLS).listen()`, `KeyboardListener(SPELLS).listen()` → 주문 key 또는 None
- `ascii_art.monster.image_to_ascii(path, width=40) -> str`, `ascii_art.spell_text.spell_banner(text) -> str` (영어만)
- `ui.screen.render(state, monster_art, banner=None, logs=(), hit=False, prompt="")`, `ui.screen.show(...)` 같은 인자
  - ui는 게임 로직을 계산하지 않는다
