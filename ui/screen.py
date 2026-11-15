"""Rich를 사용해 턴제 전투 화면을 그린다."""
import sys
import time

from rich.console import Console, Group
from rich import box
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from battle.spells import SPELLS

console = Console(force_terminal=True, legacy_windows=False)


def _get_hp_color(current, maximum):
    """체력 비율에 따른 진행 바 색상을 돌려준다."""
    if maximum <= 0:
        return "bright_red"

    rate = current / maximum
    if rate >= 0.7:
        return "cyan"
    if rate < 0.3:
        return "red"
    return "yellow"


def _hp_bar(label, hp, max_hp, color=None, width=14):
    """자원 수치와 진행 바를 한 줄로 만든다."""
    color = color or _get_hp_color(hp, max_hp)
    total = max(max_hp, 1)
    completed = max(0, min(hp, total))
    displayed_max = max(max_hp, 0)

    row = Table.grid(padding=(0, 1))
    row.add_column(no_wrap=True)
    row.add_column()
    row.add_column(justify="right", no_wrap=True)
    row.add_row(
        Text(label, style="bold white"),
        ProgressBar(total=total, completed=completed, width=width,
                    complete_style=color, finished_style=color),
        Text(f"{hp}/{displayed_max}", style=f"bold {color}"),
    )
    return row


def _mana_cost_text():
    """주문별 마나 비용을 표시하며 아직 없는 데이터는 명시한다."""
    costs = []
    for key, spell in SPELLS.items():
        mana_cost = getattr(spell, "mana_cost", None)
        cost_text = str(mana_cost) if mana_cost is not None else "N/A"
        costs.append(f"{key}({cost_text})")
    if not costs:
        return ("주문 마나 비용 데이터가 없습니다.",)

    midpoint = (len(costs) + 1) // 2
    return (
        "MP: " + " / ".join(costs[:midpoint]),
        "     " + " / ".join(costs[midpoint:]) if costs[midpoint:] else "",
    )


def _compact_monster_art(monster_art, max_lines):
    """아트의 바깥 공백을 정리하고 표시 줄 수를 제한한다."""
    lines = monster_art.strip("\n").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    if max_lines == 1:
        return lines[0]
    return "\n".join((*lines[:max_lines - 1], "..."))


def render(state, monster_art, banner=None, logs=(), hit=False, prompt=""):
    """전투 상태를 Rich 렌더러블로 만든다."""
    max_art_lines = 6 if console.height < 32 else 10
    monster_art = _compact_monster_art(monster_art, max_art_lines)
    monster = Panel(
        Text(monster_art, style="bold red" if hit else "white",
             justify="center"),
        title=f"[bold white] {state.monster_name} [/]",
        subtitle="[bold red]HIT![/]" if hit else "[dim]ENEMY[/]",
        box=box.ROUNDED,
        border_style="bold red" if hit else "bright_black",
        padding=(0, 1),
    )

    shield_badge = (
        Text(" SHIELD ACTIVE ", style="bold white on bright_black")
        if state.shield
        else Text(" SHIELD OFF ", style="dim")
    )
    player_mp = getattr(state, "player_mp", None)
    player_max_mp = getattr(state, "player_max_mp", None)
    mp_bar = (
        _hp_bar("MP", player_mp, player_max_mp, color="bright_blue", width=8)
        if player_mp is not None and player_max_mp is not None
        else Text("MP DATA UNAVAILABLE", style="bold yellow")
    )
    player_resources = Table.grid(padding=(0, 1))
    player_resources.add_column(ratio=1)
    player_resources.add_column(ratio=1)
    player_resources.add_row(
        _hp_bar("PLAYER", state.player_hp, state.player_max_hp),
        mp_bar,
    )
    hp_row = Table.grid(expand=True, padding=(0, 2))
    hp_row.add_column(ratio=2)
    hp_row.add_column(ratio=1)
    hp_row.add_row(
        player_resources,
        _hp_bar("MONSTER", state.monster_hp, state.monster_max_hp),
    )

    status_footer = Table.grid(expand=True)
    status_footer.add_column(ratio=1)
    status_footer.add_column(justify="right")
    status_footer.add_row(
        Text.assemble(
            ("TURN ", "bold white"),
            (str(state.turn), "bold white"),
        ),
        shield_badge,
    )
    status = Panel(
        Group(hp_row, status_footer),
        title="[bold white] BATTLE STATUS [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        padding=(0, 1),
    )

    spell_banner = (banner or "주문을 기다리는 중...").replace("\n", " | ")
    spell_text = Text(spell_banner, justify="center", no_wrap=True)
    spell_text.truncate(max(console.width - 8, 1), overflow="ellipsis")
    if banner:
        spell_text.stylize("bold red" if hit else "bold white")
    else:
        spell_text.stylize("dim")
    spell = Panel(
        spell_text,
        title="[bold white] SPELL | 주문 발동 [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        padding=(0, 1),
    )

    recent_logs = list(logs)[-2:]
    log_content = Text()
    if recent_logs:
        for index, log_line in enumerate(recent_logs):
            if index:
                log_content.append("\n")
            style = (
                "bold bright_red"
                if "마나가 부족하다" in log_line
                else "white"
            )
            log_content.append(log_line, style=style)
    else:
        log_content.append("전투 기록이 없습니다.", style="white")
    log = Panel(
        log_content,
        title="[bold white] BATTLE LOG · 최근 기록 [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        height=4,
        padding=(0, 1),
    )
    prompt_title = Text(" ACTION | ", style="bold white")
    prompt_title.append(prompt or "입력 대기 중...", style="white")
    prompt_title.truncate(max(console.width // 2 - 4, 1), overflow="ellipsis")
    prompt_content = Group(
        *(Text(line, style="cyan", justify="center", no_wrap=True)
          for line in _mana_cost_text())
    )
    prompt_panel = Panel(
        prompt_content,
        title=prompt_title,
        box=box.ROUNDED,
        border_style="bright_black",
        height=4,
        padding=(0, 1),
    )

    bottom = Table.grid(expand=True, padding=(0, 1))
    bottom.add_column(ratio=1)
    bottom.add_column(ratio=1)
    bottom.add_row(log, prompt_panel)

    return Group(monster, status, spell, bottom)


def show(*args, **kwargs):
    """현재 화면을 지우고 전투 화면을 다시 그린다."""
    console.clear()
    console.print(render(*args, **kwargs))


def _hit_monster_art(monster_art):
    """아트에 얼굴 문자가 있으면 피격 표정으로 바꾼다."""
    for normal, hit in (
        ("( o o )", "(>_<)"),
        ("(o o)", "(>_<)"),
        ("( O O )", "(>_<)"),
        ("(O O)", "(>_<)"),
        ("(o_o)", "(>_<)"),
    ):
        if normal in monster_art:
            return monster_art.replace(normal, hit)
    return f"***\n{monster_art}\n***"


def play_turn_sequence(state, monster_art, spell_name, kind, logs=(),
                       monster_hit=False, player_hit=False, prompt=""):
    """미리 계산된 전투 결과를 바꾸지 않고 화면 연출만 재생한다."""
    spell_frames = {
        "attack": (
            "  >=====>",
            "      >>>====>",
            "             >>>***",
        ),
        "shield": (
            "     [===]",
            "   [=======]",
            " [===========]",
        ),
        "heal": (
            "      +",
            "    + + +",
            "  + + + + +",
        ),
    }
    if kind not in spell_frames:
        raise ValueError(f"알 수 없는 주문 종류: {kind}")

    for frame in spell_frames[kind]:
        show(
            state,
            monster_art,
            banner=f"[{spell_name}]  {frame}",
            logs=logs,
            prompt=prompt or "주문 발동!",
        )
        time.sleep(0.12)

    if kind == "attack" and monster_hit:
        hit_art = _hit_monster_art(monster_art)
        for banner in (
            "*** IMPACT! ***",
            "* CRITICAL HIT *",
            ".  '  *  +  *  '  .",
        ):
            show(
                state,
                hit_art,
                banner=banner,
                logs=logs,
                hit=True,
                prompt="몬스터 피격!",
            )
            time.sleep(0.1)
            show(
                state,
                monster_art,
                banner=banner,
                logs=logs,
                prompt="몬스터 피격!",
            )
            time.sleep(0.1)

    if player_hit:
        for banner in ("!!! COUNTER ATTACK !!!", "플레이어가 공격받았습니다!"):
            show(
                state,
                monster_art,
                banner=banner,
                logs=logs,
                hit=True,
                prompt="플레이어 피격!",
            )
            time.sleep(0.1)
            show(
                state,
                monster_art,
                banner=banner,
                logs=logs,
                prompt="플레이어 피격!",
            )
            time.sleep(0.1)

    final_banner = "VICTORY!" if state.monster_hp <= 0 else None
    show(
        state,
        monster_art,
        banner=final_banner,
        logs=logs,
        prompt=prompt or "입력 대기 중...",
    )


if __name__ == "__main__":
    from types import SimpleNamespace

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    test_state = SimpleNamespace(
        monster_name="화염 슬라임",
        player_hp=57,
        player_max_hp=100,
        player_mp=25,
        player_max_mp=40,
        monster_hp=20,
        monster_max_hp=80,
        shield=True,
        turn=4,
    )
    test_art = "      .---.\n     ( o o )\n      \\___/"
    test_cases = (
        ("FIREBALL", "attack", True, False),
        ("SHIELD", "shield", False, False),
        ("HEAL", "heal", False, True),
    )
    for spell_name, kind, monster_hit, player_hit in test_cases:
        test_logs = [
            "전투 결과는 battle.engine에서 계산되었습니다.",
            f"{spell_name} 효과 기록",
            "마나가 부족하다! 마나가 회복될 때까지 주문을 사용할 수 없다.",
        ]
        play_turn_sequence(
            test_state,
            test_art,
            spell_name,
            kind,
            logs=test_logs,
            monster_hit=monster_hit,
            player_hit=player_hit,
            prompt="다음 주문을 입력하세요",
        )
