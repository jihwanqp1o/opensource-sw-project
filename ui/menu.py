"""전투 밖 화면: 타이틀(메인), 주문 목록, 결과, 테스트 모드 표시줄. 받은 값만 보여 준다."""
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ascii_art.spell_text import spell_banner

TITLE = "VOICE SHELL"
SUBTITLE = "터미널 속 마법사"
TAGLINE = "키보드가 고장 난 낡은 터미널. 목소리로 명령을 외쳐 시스템을 복구하세요."
GREEN = "bright_green"


def title_screen():
    """타이틀(메인) 화면. 메뉴 키는 main.py에서 받는다."""
    menu = Table.grid(padding=(0, 2))
    menu.add_row(Text("[Enter]", style=f"bold {GREEN}"), Text("시스템 복구 시작"))
    menu.add_row(Text("[H]", style=f"bold {GREEN}"), Text("주문 목록"))
    menu.add_row(Text("[Q]", style=f"bold {GREEN}"), Text("종료"))

    return Panel(Group(
        Text(""),
        Align.center(Text(spell_banner(TITLE), style=f"bold {GREEN}")),
        Align.center(Text(SUBTITLE, style="bold white")),
        Text(""),
        Align.center(Text(TAGLINE, style="dim")),
        Text(""),
        Align.center(menu),
        Text(""),
    ), border_style=GREEN, title="[bold] admin@voice-shell:~ [/]")


def spell_list_screen(spells):
    """주문마다 말하는 법과 효과를 보여 준다."""
    table = Table(border_style=GREEN, header_style=f"bold {GREEN}", expand=True)
    table.add_column("주문")
    table.add_column("말하는 법")
    table.add_column("종류")
    table.add_column("위력", justify="right")
    for spell in spells.values():
        table.add_row(spell.display, " / ".join(spell.phrases), spell.kind, str(spell.power))

    return Panel(Group(
        table,
        Text(""),
        Text("주문을 말하고 잠깐 멈추면 인식됩니다.  [Enter] 돌아가기", style="dim"),
    ), title="[bold] 주문 목록 [/]", border_style=GREEN)


def result_screen(won, stats):
    """전투 결과. stats: 걸린 초, 턴 수, 주문별 사용 횟수, 인식 성공·실패 횟수"""
    headline = "SYSTEM RESTORED" if won else "SEGMENTATION FAULT"
    color = GREEN if won else "bright_red"

    table = Table.grid(padding=(0, 3))
    table.add_row("걸린 시간", f"{stats['seconds']:.0f}초")
    table.add_row("턴 수", str(stats["turns"]))
    used = ", ".join(f"{key} {n}회" for key, n in stats["spells"].most_common()) or "-"
    table.add_row("사용한 주문", used)
    total = stats["recognized"] + stats["missed"]
    table.add_row("명령 인식", f"{stats['recognized']}/{total}회" if total else "-")

    return Panel(Group(
        Text(""),
        Align.center(Text(spell_banner(headline), style=f"bold {color}")),
        Text(""),
        Align.center(table),
        Text(""),
        Align.center(Text("[Enter] 타이틀로", style="dim")),
    ), border_style=color)


def test_banner(state, input_mode):
    """테스트 모드에서 화면 맨 위에 붙는 한 줄. 시연 화면과 한눈에 구분된다."""
    return Text(
        f" TEST MODE | 입력: {input_mode} | 플레이어 {state.player_hp}/{state.player_max_hp}"
        f" | 몬스터 {state.monster_hp}/{state.monster_max_hp} | 턴 {state.turn}"
        f" | 실드 {'ON' if state.shield else 'OFF'} ",
        style="bold black on yellow",
    )


if __name__ == "__main__":
    # 단독 실행: python -m ui.menu  (화면 네 개를 차례로 출력)
    from collections import Counter
    from types import SimpleNamespace

    from battle.spells import SPELLS
    from ui.screen import console

    console.print(title_screen())
    console.print(spell_list_screen(SPELLS))
    console.print(result_screen(True, {"seconds": 83, "turns": 5, "recognized": 5, "missed": 1,
                                       "spells": Counter(fireball=3, shield=1, heal=1)}))
    fake = SimpleNamespace(player_hp=70, player_max_hp=100, monster_hp=40, monster_max_hp=80,
                           turn=3, shield=False)
    console.print(test_banner(fake, "키보드"))
