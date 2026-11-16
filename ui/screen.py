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


# 주문 큰 글씨(pyfiglet standard 글꼴)는 최대 6줄이다. 칸 높이를 고정해 화면이 들썩이지 않게 한다.
SPELL_LINES = 6
LOG_LINES = 3


def _mana_cost_text():
    """주문별 마나 비용 한 줄. 마나 데이터가 아직 없으면 None (시연 화면에 빈 값을 보이지 않는다)."""
    costs = [f"{key}({spell.mana_cost})" for key, spell in SPELLS.items()
             if getattr(spell, "mana_cost", None) is not None]
    return "MP: " + " / ".join(costs) if costs else None


def _art_line_budget():
    """창 높이에서 다른 칸을 빼고 몬스터 그림에 쓸 수 있는 줄 수 (최대화한 49줄 창에서는 잘리지 않음)."""
    fixed = 4 + (SPELL_LINES + 2) + (LOG_LINES + 2) + 2 + 2  # 상태, 주문, 기록, 몬스터 테두리, 입력 줄
    return max(4, console.height - fixed)


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
    monster_art = _compact_monster_art(monster_art, _art_line_budget())
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
    # 마나 바는 마나 데이터가 있을 때만 보여 준다 (1단계 #31 이후)
    resources = [_hp_bar("PLAYER", state.player_hp, state.player_max_hp)]
    if player_mp is not None and player_max_mp is not None:
        resources.append(_hp_bar("MP", player_mp, player_max_mp, color="bright_blue", width=8))
    player_resources = Table.grid(padding=(0, 1))
    for _ in resources:
        player_resources.add_column(ratio=1)
    player_resources.add_row(*resources)
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

    # 큰 글씨는 여러 줄 그대로 보여 주고, 창이 좁으면 줄마다 오른쪽만 자른다
    spell_text = Text(banner or "주문을 기다리는 중...", justify="center",
                      no_wrap=True, overflow="crop")
    if banner:
        spell_text.stylize("bold red" if hit else "bold white")
    else:
        spell_text.stylize("dim")
    spell = Panel(
        spell_text,
        title="[bold white] SPELL | 주문 발동 [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        height=SPELL_LINES + 2,
        padding=(0, 1),
    )

    recent_logs = list(logs)[-LOG_LINES:]
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
        height=LOG_LINES + 2,
        padding=(0, 1),
    )
    # 입력 안내는 잘리지 않게 칸 안에 보여 주고, 마나 비용은 데이터가 있을 때만 덧붙인다
    prompt_lines = [Text(prompt or "입력 대기 중...", style="bold white", justify="center")]
    mana_text = _mana_cost_text()
    if mana_text:
        prompt_lines.append(Text(mana_text, style="cyan", justify="center", no_wrap=True))
    prompt_panel = Panel(
        Group(*prompt_lines),
        title="[bold white] ACTION [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        height=LOG_LINES + 2,
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
