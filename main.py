"""게임 시작점. 각 모듈을 연결만 한다. (연결 규칙: docs/INTERFACES.md)

실행: python main.py            (마이크)
      python main.py --keyboard (키보드로 테스트)
"""
import argparse
import time

import config
from ascii_art.monster import image_to_ascii
from ascii_art.spell_text import spell_banner
from battle.engine import monster_turn, new_battle, player_turn, winner
from battle.spells import SPELLS
from ui import screen
from voice.recognizer import KeyboardListener, VoiceListener


def make_listener(mode):
    if mode == "keyboard":
        return KeyboardListener(SPELLS)
    return VoiceListener(config.VOSK_MODEL_PATH, SPELLS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyboard", action="store_true", help="마이크 대신 키보드로 주문 입력")
    args = parser.parse_args()
    mode = "keyboard" if args.keyboard else config.INPUT_MODE

    listener = make_listener(mode)
    art = image_to_ascii(config.MONSTER_IMAGE, config.MONSTER_ART_WIDTH)
    state = new_battle()
    logs = []
    action = "입력하세요" if mode == "keyboard" else "외치세요"
    prompt = f"주문을 {action}: " + " / ".join(SPELLS)

    while winner(state) is None:
        # 1. 영창
        screen.show(state, art, logs=logs, prompt=prompt)
        spell_key = listener.listen()
        if spell_key is None:
            logs.append("...주문을 알아듣지 못했다. 다시!")
            continue

        # 2. 주문 발동과 피격 연출
        spell = SPELLS[spell_key]
        logs.append(player_turn(state, spell_key))
        screen.show(state, art, banner=spell_banner(spell.display), logs=logs,
                    hit=spell.kind == "attack")
        time.sleep(config.EFFECT_DELAY)
        if winner(state):
            break

        # 3. 몬스터 반격
        logs.append(monster_turn(state))
        screen.show(state, art, logs=logs)
        time.sleep(config.EFFECT_DELAY)

    result = "VICTORY" if winner(state) == "player" else "GAME OVER"
    screen.show(state, art, banner=spell_banner(result), logs=logs)


if __name__ == "__main__":
    main()
