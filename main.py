"""게임 시작점. 각 모듈을 연결만 한다. (연결 규칙: docs/INTERFACES.md)

실행: python main.py         플레이 모드 (시연용: 오프닝 → 타이틀 → 전투 → 결과, 마이크)
      python main.py --demo  플레이 모드 + 빠른 모드 (몬스터 체력을 줄여 2분 안팎에 끝남)
      python main.py --test  테스트 모드 (개발용: 바로 전투, 키보드, 화면 위에 TEST MODE)
"""
import argparse
import os
import sys
import time
from collections import Counter

# 영어 Windows(cp1252) 등에서도 한글 출력이 멈추지 않게 항상 UTF-8로 내보낸다
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")

import config
from ascii_art.intro import boot_lines
from ascii_art.monster import image_to_ascii
from ascii_art.spell_text import spell_banner
from battle.engine import (STAGES, apply_upgrade, get_upgrade_prompt, monster_turn, new_battle,
                           player_turn, winner)
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


def choose_upgrade(state):
    """스테이지를 깨면 업그레이드 화면을 보여 주고 1/2/3 중 하나를 받아 적용한다."""
    while True:
        key = show_page(menu.upgrade_screen(state, get_upgrade_prompt(), len(STAGES)))
        try:
            return apply_upgrade(state, key)
        except ValueError:
            continue  # 1/2/3이 아니면 다시 묻는다


def maximize_window():
    """Windows 콘솔 창을 최대화하고 제목을 바꾼다. 게임 화면이 40줄 정도라 기본 크기 창에서는 잘린다."""
    if os.name != "nt" or not sys.stdout.isatty():
        return
    import ctypes

    ctypes.windll.kernel32.SetConsoleTitleW("VOICE SHELL")
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 3)  # 3 = 최대화
        time.sleep(0.3)  # 창 크기가 바뀐 뒤에 화면 크기를 다시 읽게 기다린다


def play_intro():
    """부팅 오프닝을 한 줄씩 보여 준다. 아무 키나 누르면 건너뛴다. 자동 입력(파이프)일 때는 건너뛴다."""
    if not sys.stdin.isatty():
        return
    try:
        import msvcrt  # Windows에서 키 눌림 확인
    except ImportError:
        msvcrt = None

    screen.console.clear()
    for line, delay in boot_lines():
        screen.console.print(line)
        end = time.monotonic() + delay
        while time.monotonic() < end:
            if msvcrt and msvcrt.kbhit():
                msvcrt.getwch()  # 누른 키는 버린다
                return
            time.sleep(0.05)


def run_battle(listener, art, input_mode, test_mode, monster_hp_rate=1.0):
    """4연전 한 판을 진행하고 (이겼는지, 결과 통계)를 돌려준다."""
    state = new_battle(monster_hp_rate)
    logs = []
    stats = {"spells": Counter(), "recognized": 0, "missed": 0}
    start = time.monotonic()
    action = "입력하세요" if input_mode == "keyboard" else "외치세요"

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
        prompt = f"STAGE {state.stage}/{len(STAGES)} | 주문을 {action}: " + " / ".join(SPELLS)
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
        if state.awaiting_upgrade:
            # 중간 스테이지를 깨면 몬스터 반격 없이 업그레이드를 고르고 다음 몬스터로 넘어간다
            logs.append(choose_upgrade(state))
            continue

        # 3. 몬스터 반격
        logs.append(monster_turn(state))
        draw(logs=logs)
        time.sleep(config.EFFECT_DELAY)

    stats["seconds"] = time.monotonic() - start
    stats["turns"] = state.turn
    stats["stage"] = f"{state.stage}/{len(STAGES)}"
    return winner(state) == "player", stats


def show_page(renderable):
    """전투 밖 화면을 보여 주고 키 입력 하나를 받는다."""
    screen.console.clear()
    screen.console.print(renderable)
    return input("> ").strip().lower()


def play_mode(listener, art, input_mode, monster_hp_rate):
    """시연용 흐름: 오프닝 → 타이틀 → 전투 → 결과 → 타이틀"""
    play_intro()
    while True:
        key = show_page(menu.title_screen(demo=monster_hp_rate != 1.0))
        if key == "q":
            return
        if key == "h":
            show_page(menu.spell_list_screen(SPELLS))
        elif key == "":
            # 시연 중 실수로 다른 키를 눌러도 시작되지 않게 Enter만 받는다
            won, stats = run_battle(listener, art, input_mode, test_mode=False,
                                    monster_hp_rate=monster_hp_rate)
            show_page(menu.result_screen(won, stats))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", "--keyboard", dest="test", action="store_true",
                        help="테스트 모드: 메뉴 없이 바로 전투, 키보드 입력, 화면 위에 TEST MODE")
    parser.add_argument("--demo", action="store_true",
                        help="시연용 빠른 모드: 몬스터 체력을 줄여 2분 안팎에 끝난다 (배율: DEMO_HP_RATE)")
    args = parser.parse_args()

    maximize_window()
    input_mode = "keyboard" if args.test else config.INPUT_MODE
    monster_hp_rate = config.DEMO_HP_RATE if args.demo else 1.0
    listener = make_listener(input_mode)
    art = image_to_ascii(config.MONSTER_IMAGE, config.MONSTER_ART_WIDTH)

    try:
        if args.test:
            won, _ = run_battle(listener, art, input_mode, test_mode=True,
                                monster_hp_rate=monster_hp_rate)
            screen.console.print(spell_banner("VICTORY" if won else "GAME OVER"))
        else:
            play_mode(listener, art, input_mode, monster_hp_rate)
    except KeyboardInterrupt:
        pass  # Ctrl+C로 끄면 오류 메시지 없이 끝낸다


if __name__ == "__main__":
    main()
