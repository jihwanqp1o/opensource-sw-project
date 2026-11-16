"""전투 밖 화면: 타이틀(메인), 주문 목록, 결과, 상점, 던전 갈림길·방, 테스트 모드 표시줄. 받은 값만 보여 준다."""
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ascii_art.spell_text import spell_banner
from world.dungeon import KIND_LABELS

TITLE = "VOICE SHELL"
SUBTITLE = "터미널 속 마법사"
TAGLINE = "키보드가 고장 난 낡은 터미널. 목소리로 명령을 외쳐 시스템을 복구하세요."
GREEN = "bright_green"


def title_screen(demo=False):
    """타이틀(메인) 화면. 메뉴 키는 main.py에서 받는다. demo=True면 오른쪽 아래에 빠른 모드 표시."""
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
    ), border_style=GREEN, title="[bold] admin@voice-shell:~ [/]",
        subtitle="[dim] DEMO [/]" if demo else None, subtitle_align="right")


def spell_list_screen(spells):
    """주문마다 말하는 법, 마나, 효과, 얻는 방법을 보여 준다."""
    table = Table(border_style=GREEN, header_style=f"bold {GREEN}", expand=True)
    table.add_column("주문")
    table.add_column("말하는 법")
    table.add_column("MP", justify="right")
    table.add_column("효과")
    table.add_column("얻는 법")
    for spell in spells.values():
        table.add_row(spell.display, " / ".join(spell.phrases), str(spell.mana_cost), spell.desc,
                      "처음부터" if spell.starter else "상점")

    return Panel(Group(
        table,
        Text(""),
        Text("주문을 말하고 잠깐 멈추면 인식됩니다. 마나는 몬스터 턴마다 10 회복.  [Enter] 돌아가기",
             style="dim"),
    ), title="[bold] 주문 목록 [/]", border_style=GREEN)


def result_screen(won, stats):
    """전투 결과. stats: 걸린 초, 턴 수, 주문별 사용 횟수, 인식 성공·실패 횟수"""
    headline = "SYSTEM RESTORED" if won else "SEGMENTATION FAULT"
    color = GREEN if won else "bright_red"

    table = Table.grid(padding=(0, 3))
    if "stage" in stats:
        table.add_row("도달 스테이지", stats["stage"])
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


def upgrade_screen(state, options, total_stages):
    """스테이지를 깬 뒤 상점(패키지 저장소). options: [(번호, 설명)], battle.engine.get_shop_options에서 받는다."""
    bonus = Table.grid(padding=(0, 3))
    bonus.add_row("공격력", f"+{state.bonus_attack}")
    bonus.add_row("체력", f"{state.player_hp}/{state.player_max_hp}")
    if hasattr(state, "player_mp"):
        bonus.add_row("마나", f"{state.player_mp}/{state.player_max_mp}")
    bonus.add_row("힐량 / 크리티컬", f"+{state.bonus_heal} / +{state.bonus_crit:.0%}")
    if hasattr(state, "known_spells"):
        bonus.add_row("설치된 주문", ", ".join(state.known_spells))

    choices = Table.grid(padding=(0, 2))
    for number, label in options:
        # 4번부터는 주문 설치라 색을 달리한다
        style = "bold bright_cyan" if int(number) > 3 else "bold white"
        choices.add_row(Text(f"[{number}]", style=f"bold {GREEN}"), Text(label, style=style))

    return Panel(Group(
        Text(""),
        Align.center(Text(spell_banner(f"STAGE {state.stage} CLEAR"), style=f"bold {GREEN}")),
        Align.center(Text(f"[ OK ] {state.monster_name} 정리 완료 ({state.stage}/{total_stages})",
                          style="bold white")),
        Text(""),
        Align.center(bonus),
        Text(""),
        Align.center(Text("하나를 골라 스탯을 강화하거나 새 주문을 설치하세요", style="bold white")),
        Align.center(choices),
        Text(""),
        Align.center(Text("번호를 입력하고 Enter", style="dim")),
    ), title="[bold] PACKAGE STORE · 패키지 저장소 [/]", border_style=GREEN)


def fork_screen(room, exits, path, art=""):
    """던전 갈림길. room: 지금 방, exits: [(방향, 다음 방)], path: 지나온 방 목록 (world.dungeon에서 받음).
    뼈대용 기본 화면이다. 지도 모양과 꾸미기는 #40에서 정한다."""
    trail = Text(" > ".join(r.name for r in path), style="dim")
    choices = Table.grid(padding=(0, 2))
    for direction, target in exits:
        choices.add_row(Text(f"[{direction}]", style=f"bold {GREEN}"),
                        Text(target.name, style="bold white"), Text(KIND_LABELS[target.kind], style="dim"))

    return Panel(Group(
        Text(""),
        Align.center(Text(art)) if art else Text(""),
        Align.center(trail),
        Text(""),
        Align.center(Text("갈림길입니다. cd 할 폴더를 고르세요", style="bold white")),
        Align.center(choices),
        Text(""),
        Align.center(Text("방향을 외치세요 (인식이 안 되면 키보드로 치고 Enter)", style="dim")),
    ), title=f"[bold] admin@voice-shell:{room.name}$ [/]", border_style=GREEN)


def room_screen(room, log, art=""):
    """회복 샘·보물 방에 들어갔을 때. log: battle.engine.room_event가 돌려준 문장. 꾸미기는 #40에서 정한다."""
    return Panel(Group(
        Text(""),
        Align.center(Text(art)) if art else Text(""),
        Align.center(Text(KIND_LABELS[room.kind], style=f"bold {GREEN}")),
        Text(""),
        Align.center(Text(log, style="bold white")),
        Text(""),
    ), title=f"[bold] admin@voice-shell:{room.name}$ [/]", border_style=GREEN)


def test_banner(state, input_mode):
    """테스트 모드에서 화면 맨 위에 붙는 한 줄. 시연 화면과 한눈에 구분된다."""
    stage = f" | 스테이지 {state.stage}" if hasattr(state, "stage") else ""
    return Text(
        f" TEST MODE{stage} | 입력: {input_mode} | 플레이어 {state.player_hp}/{state.player_max_hp}"
        + (f" | 마나 {state.player_mp}/{state.player_max_mp}" if hasattr(state, "player_mp") else "")
        + f" | 몬스터 {state.monster_hp}/{state.monster_max_hp} | 턴 {state.turn}"
        f" | 실드 {'ON' if state.shield else 'OFF'} ",
        style="bold black on yellow",
    )


if __name__ == "__main__":
    # 단독 실행: python -m ui.menu  (화면 다섯 개를 차례로 출력)
    from collections import Counter
    from types import SimpleNamespace

    from battle.spells import SPELLS
    from ui.screen import console

    console.print(title_screen())
    console.print(spell_list_screen(SPELLS))
    console.print(result_screen(True, {"seconds": 83, "turns": 5, "recognized": 5, "missed": 1,
                                       "spells": Counter(fireball=3, shield=1, heal=1),
                                       "stage": "4/4"}))
    fake = SimpleNamespace(player_hp=70, player_max_hp=100, monster_hp=40, monster_max_hp=80,
                           turn=3, shield=False, stage=2, monster_name="버그 고블린",
                           bonus_attack=10, bonus_heal=0, bonus_crit=0.0)
    console.print(upgrade_screen(fake, [("1", "공격력 +10"), ("2", "체력 +20"), ("3", "마력"),
                                        ("4", "ice 설치 (MP 15) - 프로세스 일시정지")], 4))
    console.print(test_banner(fake, "키보드"))

    from world import dungeon
    console.print(fork_screen(dungeon.get_room("home"), dungeon.exits("home"), [dungeon.get_room("home")]))
    console.print(room_screen(dungeon.get_room("home_backup"), "[ OK ] 백업 파일 복원: 체력 +20, 마나 +20"))
