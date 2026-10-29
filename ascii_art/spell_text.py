"""주문 이름을 큰 아스키 글씨로 만든다. pyfiglet 글꼴에는 한글이 없으므로 영어만 넣는다."""
import pyfiglet

FONT = "standard"


def spell_banner(text) -> str:
    return pyfiglet.figlet_format(text, font=FONT).rstrip()


if __name__ == "__main__":
    # 단독 실행: python -m ascii_art.spell_text
    print(spell_banner("FIREBALL"))
