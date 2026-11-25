"""전투 밖 화면: 타이틀(메인), 주문 목록, 결과, 상점, 던전 갈림길·방, 테스트 모드 표시줄. 받은 값만 보여 준다."""
import re

from rich.align import Align
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ascii_art.spell_text import spell_banner
from ui.screen import console
from world.dungeon import KIND_LABELS

TITLE = "VOICE SHELL"
SUBTITLE = "터미널 속 마법사"
TAGLINE = "키보드가 고장 난 낡은 터미널. 목소리로 명령을 외쳐 시스템을 복구하세요."
GREEN = "bright_green"
FRAME_WIDTH = 92
FRAME_HEIGHT = 32


def _frame(content, title, border_style=GREEN, subtitle=None):
    """화면을 비우고 고정 너비 프레임을 중앙에 배치한다."""
    console.clear()
    panel = Panel(
        content,
        title=title,
        subtitle=subtitle,
        border_style=border_style,
        box=box.DOUBLE,
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        padding=(1, 3),
    )
    return Align.center(panel, vertical="middle")


def title_screen(demo=False):
    """타이틀(메인) 화면. 메뉴 키는 main.py에서 받는다. demo=True면 오른쪽 아래에 빠른 모드 표시."""
    menu = Table.grid(padding=(0, 2))
    menu.add_row(Text("[Enter]", style="bold black on bright_green"), Text("시스템 복구 시작", style="white"))
    menu.add_row(Text("[H]", style="bold black on bright_green"), Text("주문 목록", style="white"))
    menu.add_row(Text("[Q]", style="bold black on bright_green"), Text("종료", style="white"))

    return _frame(Group(
        Align.center(Text(spell_banner(TITLE), style=f"bold {GREEN}")),
        Align.center(Text(SUBTITLE, style="bold white")),
        Align.center(Text(TAGLINE, style="dim green")),
        Align.center(menu),
    ), "[bold bright_green] admin@voice-shell:~ [/]",
       subtitle="[bold bright_cyan] DEMO [/]" if demo else None)


def spell_list_screen(spells):
    """주문마다 말하는 법, 마나, 효과, 얻는 방법을 보여 준다."""
    table = Table(
        border_style="bright_cyan",
        header_style="bold bright_green",
        expand=True,
        box=box.HEAVY,
        padding=(0, 1),
    )
    table.add_column("주문", style="bold bright_green", no_wrap=True)
    table.add_column("말하는 법", style="bright_cyan")
    table.add_column("MP", justify="right", style="bold bright_yellow", no_wrap=True)
    table.add_column("효과", style="white")
    table.add_column("얻는 법", style="dim green", no_wrap=True)
    for spell in spells.values():
        table.add_row(spell.display, " / ".join(spell.phrases), str(spell.mana_cost), spell.desc,
                      "처음부터" if spell.starter else "상점")

    return _frame(Group(
        table,
        Align.center(Text(
            "주문을 말하고 잠깐 멈추면 인식됩니다. 마나는 몬스터 턴마다 10 회복.",
            style="dim green",
        )),
        Align.center(Text("[Enter] 돌아가기", style="bold bright_cyan")),
    ), "[bold bright_green] 주문 목록 | SPELL INDEX [/]")


def result_screen(won, stats):
    """전투 결과. stats: 걸린 초, 턴 수, 주문별 사용 횟수, 인식 성공·실패 횟수"""
    headline = "SYSTEM RESTORED" if won else "SEGMENTATION FAULT"
    color = GREEN if won else "bright_red"

    table = Table.grid(padding=(0, 2))
    table.add_column(style="white")
    table.add_column(style="bold bright_cyan")
    table.add_row("걸린 시간", f"{stats['seconds']:.0f}초")
    table.add_row("턴 수", str(stats["turns"]))
    used = ", ".join(f"{key} {n}회" for key, n in stats["spells"].most_common()) or "-"
    table.add_row("사용한 주문", used)
    total = stats["recognized"] + stats["missed"]
    table.add_row("명령 인식", f"{stats['recognized']}/{total}회" if total else "-")

    stage_line = (
        Align.center(Text(f"도달 스테이지   {stats['stage']}", style=f"bold {GREEN}"))
        if "stage" in stats else None
    )
    return _frame(Group(
        Align.center(Text(spell_banner(headline), style=f"bold {color}")),
        *([stage_line] if stage_line else []),
        Align.center(table),
        Align.center(Text("[Enter] 타이틀로", style="bold bright_cyan")),
    ), f"[bold {color}] SYSTEM REPORT [/]", border_style=color)


def upgrade_screen(state, options, total_stages):
    """스테이지를 깬 뒤 상점(패키지 저장소). options: [(번호, 설명)], battle.engine.get_shop_options에서 받는다."""
    status = Table.grid(padding=(0, 1))
    status.add_column()
    status.add_column()
    status.add_row(
        Text("STAGE", style=f"bold {GREEN}"),
        Text(f"{state.stage}/{total_stages} CLEAR", style=f"bold {GREEN}"),
    )
    status.add_row(
        Text("HP", style=f"bold {GREEN}"),
        Text(f"{state.player_hp}/{state.player_max_hp}", style=GREEN),
    )
    if hasattr(state, "player_mp"):
        status.add_row(
            Text("MP", style=f"bold {GREEN}"),
            Text(f"{state.player_mp}/{state.player_max_mp}", style="bright_blue"),
        )
    status.add_row(
        Text("BONUS", style=f"bold {GREEN}"),
        Text(
            f"ATK +{state.bonus_attack} | HEAL +{state.bonus_heal} | "
            f"CRIT +{state.bonus_crit:.0%}",
            style=GREEN,
        ),
    )
    if hasattr(state, "known_spells"):
        status.add_row(
            Text("INSTALLED", style=f"bold {GREEN}"),
            Text(", ".join(state.known_spells) or "-", style=GREEN,
                 no_wrap=True, overflow="crop"),
        )

    choices = Table.grid(padding=(0, 2))
    choices.add_column(no_wrap=True)
    choices.add_column(no_wrap=True, overflow="crop")
    for number, label in options:
        choices.add_row(
            Text(f"[{number}]", style="bold black on bright_green"),
            Text(label, style="white", no_wrap=True, overflow="crop"),
        )

    return _frame(Group(
        Align.center(Text(
            f"[ OK ] {state.monster_name} 정리 완료",
            style=f"bold {GREEN}",
            no_wrap=True,
            overflow="crop",
        )),
        Align.center(status),
        Align.center(Text(
            "하나를 골라 스탯을 강화하거나 새 주문을 설치하세요",
            style="white",
            no_wrap=True,
            overflow="crop",
        )),
        Align.center(choices),
        Align.center(Text(
            "번호를 입력하고 Enter",
            style="bold bright_cyan",
            no_wrap=True,
            overflow="crop",
        )),
    ), "[bold bright_green] PACKAGE STORE | 패키지 저장소 [/]")


def fork_screen(room, exits, path, art=""):
    """던전 갈림길. 지나온 방과 현재 위치, 선택 가능한 디렉터리를 보여 준다."""
    visited_rooms = list(path)
    if not visited_rooms or visited_rooms[-1].key != room.key:
        visited_rooms.append(room)

    tree = Text()
    for index, visited in enumerate(visited_rooms):
        if index:
            tree.append("    " * (index - 1) + "└── ", style="dim green")
        current = index == len(visited_rooms) - 1
        marker = "[>]" if current else "[v]"
        style = "bold bright_green" if current else "bright_green"
        tree.append(f"{marker} ", style=style)
        tree.append(visited.name, style=style)
        tree.append("\n")

    for index, (direction, target) in enumerate(exits):
        is_last = index == len(exits) - 1
        prefix = "└── " if is_last else "├── "
        tree.append("    " * len(visited_rooms) + prefix, style="dim green")
        tree.append(f"{direction.upper()} -> ", style="bold bright_cyan")
        tree.append(f"{target.name}\n", style="bright_green")

    map_panel = Panel(
        tree,
        title="[bold bright_green] DIRECTORY MAP [/]",
        border_style=GREEN,
        box=box.ASCII,
        width=84,
        padding=(0, 1),
    )

    choices = Table(
        box=box.ASCII,
        border_style=GREEN,
        header_style="bold bright_green",
        expand=True,
        padding=(0, 1),
    )
    choices.add_column("방향", style="bold bright_cyan", no_wrap=True)
    choices.add_column("대상 경로", style="bright_green")
    choices.add_column("방 종류", style="dim green")
    for direction, target in exits:
        choices.add_row(direction.upper(), f"cd {target.name}", KIND_LABELS[target.kind])

    content = Group(
        Align.center(Text(art, style="bright_cyan")) if art else Text(""),
        Align.center(map_panel),
        Align.center(Text("갈림길 | 다음 디렉터리를 선택하세요", style="bold bright_green")),
        choices,
        Align.center(Text(
            "방향을 말하거나 키보드로 입력하고 Enter",
            style="bold bright_cyan",
        )),
    )
    return _frame(
        content,
        f"[bold bright_green] admin@voice-shell:{room.name}$ [/]",
        subtitle="[bold bright_cyan] DIRECTORY SELECT [/]",
    )


def room_screen(room, log, art=""):
    """회복 샘·보물 방과 room_event 결과를 보여 준다."""
    accents = {
        "spring": ("bright_cyan", "bright_green", "SPRING"),
        "treasure": ("bright_yellow", "bright_green", "TREASURE"),
        "monster": ("bright_green", "bright_cyan", "MONSTER"),
        "boss": ("bright_red", "bright_green", "BOSS"),
    }
    color, highlight, badge = accents.get(
        room.kind, (GREEN, "bright_cyan", room.kind.upper())
    )
    title = KIND_LABELS[room.kind]
    if not art:
        if room.kind == "spring":
            art = "       .-~~~~-.\n      /  ~~~~  \\\n     |  SPRING  |\n      \\________/"
        elif room.kind == "treasure":
            art = "       _________\n      /_______/|\n      |  $$$  |/\n      |_______|"
        elif room.kind == "boss":
            art = "       .----.\n      / .--. \\\n      | |XX| |\n      \\ '--' /\n       '----'"
        else:
            art = "      .-====-.\n     /  BUG   \\\n     | (x  x) |\n      '------'"

    message = log[len("[ OK ]"):].lstrip() if log.startswith("[ OK ]") else log
    log_text = Text("[ OK ] ", style=f"bold {GREEN}")
    message_start = len(log_text)
    log_text.append(message, style="white")
    for match in re.finditer(r"(?:체력|마나)\s*[+-]?\d+|[+-]\d+", message):
        log_text.stylize(
            f"bold {highlight}",
            message_start + match.start(),
            message_start + match.end(),
        )
    log_panel = Panel(
        Align.center(log_text),
        title="[bold bright_green] SYSTEM LOG [/]",
        border_style=GREEN,
        box=box.ASCII,
        width=84,
        padding=(0, 2),
    )
    return _frame(Group(
        Align.center(Text(art, style=color)),
        Align.center(Text(f"[ {badge} ] {title}", style=f"bold {highlight}")),
        Align.center(Text(f"cd {room.name}", style=f"bold {GREEN}")),
        log_panel,
    ), f"[bold bright_green] admin@voice-shell:{room.name}$ [/]",
       border_style=color, subtitle=f"[bold {highlight}] {room.name} | SYSTEM EVENT [/]")


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
    # 단독 실행: python -m ui.menu  (화면 예시를 차례로 출력)
    from collections import Counter
    from types import SimpleNamespace

    from battle.spells import SPELLS

    def show_test_screen(renderable):
        console.clear()
        console.print(renderable)

    previews = [
        title_screen(),
        spell_list_screen(SPELLS),
        result_screen(True, {"seconds": 83, "turns": 5, "recognized": 5, "missed": 1,
                             "spells": Counter(fireball=3, shield=1, heal=1),
                             "stage": "4/4"}),
    ]
    fake = SimpleNamespace(player_hp=70, player_max_hp=100, monster_hp=40, monster_max_hp=80,
                           turn=3, shield=False, stage=2, monster_name="버그 고블린",
                           bonus_attack=10, bonus_heal=0, bonus_crit=0.0)
    previews.append(upgrade_screen(
        fake,
        [("1", "공격력 +10"), ("2", "체력 +20"), ("3", "마력"),
         ("4", "ice 설치 (MP 15) - 프로세스 일시정지")],
        4,
    ))

    from world import dungeon
    previews.append(fork_screen(
        dungeon.get_room("home"),
        dungeon.exits("home"),
        [dungeon.get_room("home")],
    ))
    previews.append(room_screen(
        dungeon.get_room("home_backup"),
        "[ OK ] 백업 파일 복원: 체력 +20, 마나 +20",
    ))
    for preview in previews:
        show_test_screen(preview)
