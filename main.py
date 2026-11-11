"""게임 시작점. 각 모듈을 연결만 한다. (연결 규칙: docs/INTERFACES.md)

실행: python main.py         플레이 모드 (시연용: 타이틀 → 전투 → 결과, 마이크)
      python main.py --test  테스트 모드 (개발용: 바로 전투, 키보드, 화면 위에 TEST MODE)
"""
import argparse
import time
from collections import Counter

import config
from ascii_art.monster import image_to_ascii
from ascii_art.spell_text import spell_banner
from battle.engine import monster_turn, new_battle, player_turn, winner
from battle.spells import SPELLS
from ui import menu, screen
from voice.recognizer import KeyboardListener, VoiceListener


def show_listening(heard, remaining):
    """마이크로 듣는 동안 화면 맨 아래 한 줄에 남은 시간과 들린 말을 보여 준다."""
    left = f"{remaining:4.1f}초" if remaining is not None else ""
    print(f"\r  [마이크] 듣는 중... {left} | {heard}".ljust(70), end="", flush=True)


def make_listener(input_mode):
    if input_mode == "keyboard":
        return KeyboardListener(SPELLS)
    return VoiceListener(config.VOSK_MODEL_PATH, SPELLS,
                         min_confidence=config.VOICE_MIN_CONFIDENCE,
                         reject_unknown=config.VOICE_REJECT_UNKNOWN,
                         device=config.MIC_DEVICE,
                         timeout=config.VOICE_TIMEOUT,
                         on_status=show_listening)


def run_battle(listener, art, input_mode, test_mode):
    """전투 한 판을 진행하고 (이겼는지, 결과 통계)를 돌려준다."""
    state = new_battle()
    logs = []
    stats = {"spells": Counter(), "recognized": 0, "missed": 0}
    start = time.monotonic()
    action = "입력하세요" if input_mode == "keyboard" else "외치세요"
    prompt = f"주문을 {action}: " + " / ".join(SPELLS)

    def draw(**kwargs):
        if test_mode:
            # 테스트 모드는 맨 위에 TEST MODE 줄을 붙여 시연 화면과 구분한다
            screen.console.clear()
            screen.console.print(menu.test_banner(state, input_mode))
            screen.console.print(screen.render(state, art, **kwargs))
        else:
            screen.show(state, art, **kwargs)

    while winner(state) is None:
        # 1. 영창
        draw(logs=logs, prompt=prompt)
        spell_key = listener.listen()

        # 2. 주문 발동과 피격 연출 (못 알아들으면 None → player_turn이 턴을 넘긴다)
        logs.append(player_turn(state, spell_key))
        if spell_key is None:
            stats["missed"] += 1
            draw(logs=logs)
        else:
            stats["recognized"] += 1
            stats["spells"][spell_key] += 1
            spell = SPELLS[spell_key]
            draw(banner=spell_banner(spell.display), logs=logs, hit=spell.kind == "attack")
        time.sleep(config.EFFECT_DELAY)
        if winner(state):
            break

        # 3. 몬스터 반격
        logs.append(monster_turn(state))
        draw(logs=logs)
        time.sleep(config.EFFECT_DELAY)

    stats["seconds"] = time.monotonic() - start
    stats["turns"] = state.turn
    return winner(state) == "player", stats


def show_page(renderable):
    """전투 밖 화면을 보여 주고 키 입력 하나를 받는다."""
    screen.console.clear()
    screen.console.print(renderable)
    return input("> ").strip().lower()


def play_mode(listener, art, input_mode):
    """시연용 흐름: 타이틀 → 전투 → 결과 → 타이틀"""
    while True:
        key = show_page(menu.title_screen())
        if key == "q":
            return
        if key == "h":
            show_page(menu.spell_list_screen(SPELLS))
        elif key == "":
            # 시연 중 실수로 다른 키를 눌러도 시작되지 않게 Enter만 받는다
            won, stats = run_battle(listener, art, input_mode, test_mode=False)
            show_page(menu.result_screen(won, stats))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", "--keyboard", dest="test", action="store_true",
                        help="테스트 모드: 메뉴 없이 바로 전투, 키보드 입력, 화면 위에 TEST MODE")
    args = parser.parse_args()

    input_mode = "keyboard" if args.test else config.INPUT_MODE
    listener = make_listener(input_mode)
    art = image_to_ascii(config.MONSTER_IMAGE, config.MONSTER_ART_WIDTH)

    try:
        if args.test:
            won, _ = run_battle(listener, art, input_mode, test_mode=True)
            screen.console.print(spell_banner("VICTORY" if won else "GAME OVER"))
        else:
            play_mode(listener, art, input_mode)
    except KeyboardInterrupt:
        pass  # Ctrl+C로 끄면 오류 메시지 없이 끝낸다


if __name__ == "__main__":
    main()
