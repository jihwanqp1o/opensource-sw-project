"""Rich를 사용해 턴제 전투 화면을 그린다."""
import sys
import time

from rich.console import Console, Group
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from battle.engine import STAGES
from battle.spells import SPELLS

console = Console(force_terminal=True, legacy_windows=False)


def _get_hp_color(current, maximum):
    """체력 비율에 따른 진행 바 색상을 돌려준다."""
    if maximum <= 0:
        return "bright_red"

    rate = current / maximum
    if rate >= 0.7:
        return "bright_green"
    if rate < 0.3:
        return "bright_red"
    return "yellow"


def _hp_bar(label, hp, max_hp, color=None, width=14):
    """자원 수치와 진행 바를 한 줄로 만든다."""
    color = color or _get_hp_color(hp, max_hp)
    total = max(max_hp, 1)
    completed = max(0, min(hp, total))
    displayed_max = max(max_hp, 0)
    filled = round(width * completed / total)

    row = Table.grid(padding=(0, 1))
    row.add_column(no_wrap=True, overflow="crop")
    row.add_column(no_wrap=True, overflow="crop")
    row.add_column(justify="right", no_wrap=True, overflow="crop")
    row.add_row(
        Text(label, style=f"bold {color}"),
        Text("■" * filled + "□" * (width - filled), style=color, no_wrap=True),
        Text(f"{hp}/{displayed_max}", style=f"bold {color}"),
    )
    return row


# 주문 큰 글씨(pyfiglet standard 글꼴)는 최대 6줄이다. 칸 높이를 고정해 화면이 들썩이지 않게 한다.
SPELL_LINES = 6
LOG_LINES = 3


def _privilege_name(level):
    """숫자 레벨을 터미널 권한 이름으로 바꾼다."""
    if level <= 1:
        return "guest"
    if level == 2:
        return "user"
    if level == 3:
        return "admin"
    return "root"


def _mana_cost_text(state):
    """주문 비용을 두 개씩 묶고 잠긴 주문은 흐리게 만든다."""
    known = set(getattr(state, "known_spells", ()))
    level = getattr(state, "level", 1)
    rows = []
    row = Text()
    for index, (key, spell) in enumerate(SPELLS.items()):
        if index and index % 2 == 0:
            rows.append(row)
            row = Text()
        if row:
            row.append(" / ", style="bright_green")

        mana_cost = getattr(spell, "mana_cost", None)
        label = f"{key}({mana_cost})" if mana_cost is not None else key
        min_level = getattr(spell, "min_level", None)
        locked = key not in known or (min_level is not None and level < min_level)
        row.append(label, style="dim" if locked else "bright_green")
    if row:
        rows.append(row)
    return rows


def _has_experience(state):
    return (getattr(state, "experience", None) is not None
            and getattr(state, "experience_to_next", None) is not None)


def _bonus_text(state):
    """상태에 전달된 강화 수치 중 0보다 큰 항목만 표시한다."""
    bonuses = []
    attack = getattr(state, "bonus_attack", 0)
    heal = getattr(state, "bonus_heal", 0)
    crit = getattr(state, "bonus_crit", 0)
    if attack > 0:
        bonuses.append(f"공격력 +{attack}")
    if heal > 0:
        bonuses.append(f"힐량 +{heal}")
    if crit > 0:
        bonuses.append(f"크리티컬 +{crit:.0%}")
    return bonuses


def _ascii_banner(message):
    """터미널에서 깨지지 않도록 ASCII 테두리 배너를 만든다."""
    border = "+" + "-" * (len(message) + 2) + "+"
    return f"{border}\n| {message} |\n{border}"


def _art_line_budget(state, spell_height, action_lines):
    """다른 패널 높이를 고려해 몬스터 그림에 쓸 줄 수를 정한다."""
    status_lines = 2 + 2 + int(_has_experience(state)) + int(bool(_bonus_text(state)))
    bottom_lines = max(LOG_LINES + 2, action_lines + 2)
    fixed = status_lines + spell_height + bottom_lines + 2
    return max(1, console.height - fixed)


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
    logs = list(logs)
    privilege = _privilege_name(getattr(state, "level", 1))
    stage = getattr(state, "stage", 1)
    terminal_result = None
    if state.player_hp <= 0:
        terminal_result = "SEGMENTATION FAULT"
    elif stage >= len(STAGES) and state.monster_hp <= 0:
        terminal_result = "SYSTEM RESTORED"
    promotion = bool(logs and "[ OK ] PERMISSION GRANTED" in logs[-1])

    if terminal_result:
        banner_text = _ascii_banner(terminal_result)
        banner_style = "bold bright_red" if state.player_hp <= 0 else "bold bright_green"
    elif promotion:
        banner_text = _ascii_banner("PERMISSION GRANTED")
        banner_style = "bold bright_green"
    else:
        banner_text = banner
        banner_style = "bold bright_red" if hit else "bold bright_green"

    cost_rows = _mana_cost_text(state)
    action_prompt = (
        f"{privilege}@voice-shell:/home$ 주문을 외치세요"
        if not prompt or prompt.startswith("STAGE ")
        else f"{privilege}@voice-shell:/home$ {prompt}"
    )
    spell_height = SPELL_LINES + 2 if banner_text else 3
    monster_art = _compact_monster_art(
        monster_art,
        _art_line_budget(state, spell_height, len(cost_rows) + 1),
    )
    monster = Panel(
        Text(monster_art, style="bold bright_red" if hit else "bright_green",
             justify="center", no_wrap=True, overflow="crop"),
        title=f"[bold bright_green] {state.monster_name} [/]",
        subtitle="[bold bright_red]HIT![/]" if hit else "[dim]ENEMY[/]",
        box=box.ASCII,
        border_style="bright_red" if hit else "bright_green",
        padding=(0, 1),
    )

    shield_badge = (
        Text(" SHIELD ACTIVE ", style="bold bright_green")
        if state.shield
        else Text(" SHIELD OFF ", style="dim bright_green")
    )
    player_mp = getattr(state, "player_mp", None)
    player_max_mp = getattr(state, "player_max_mp", None)
    resources = [_hp_bar("PLAYER", state.player_hp, state.player_max_hp)]
    if player_mp is not None and player_max_mp is not None:
        resources.append(_hp_bar("MEM", player_mp, player_max_mp, color="bright_blue", width=6))
    player_resources = Table.grid(padding=(0, 1))
    for _ in resources:
        player_resources.add_column(ratio=1, overflow="crop")
    player_resources.add_row(*resources)
    hp_row = Table.grid(expand=True, padding=(0, 2))
    hp_row.add_column(ratio=2, overflow="crop")
    hp_row.add_column(ratio=1, overflow="crop")
    hp_row.add_row(
        player_resources,
        _hp_bar("MONSTER", state.monster_hp, state.monster_max_hp),
    )

    status_content = [hp_row]
    if _has_experience(state):
        status_content.append(_hp_bar(
            "EXP",
            state.experience,
            state.experience_to_next,
            color="bright_green",
            width=14,
        ))
    status_footer = Table.grid(expand=True)
    status_footer.add_column(ratio=1, overflow="crop")
    status_footer.add_column(justify="right", overflow="crop")
    status_footer.add_row(
        Text(
            f"STAGE {stage}/{len(STAGES)} | TURN {state.turn} | "
            f"PRIVILEGE: {privilege}",
            style="bold bright_green",
        ),
        shield_badge,
    )
    status_content.append(status_footer)
    bonuses = _bonus_text(state)
    if bonuses:
        status_content.append(Text(" | ".join(bonuses), style="bright_green"))
    status = Panel(
        Group(*status_content),
        title="[bold bright_green] BATTLE STATUS [/]",
        box=box.ASCII,
        border_style="bright_green",
        padding=(0, 1),
    )

    # 큰 글씨는 여러 줄 그대로 보여 주고, 창이 좁으면 줄마다 오른쪽만 자른다
    spell_text = Text(banner_text or "주문을 기다리는 중...", justify="center",
                      no_wrap=True, overflow="crop")
    if banner_text:
        spell_text.stylize(banner_style)
    else:
        spell_text.stylize("bright_green")
    spell = Panel(
        spell_text,
        title="[bold bright_green] SPELL | COMMAND [/]",
        box=box.ASCII,
        border_style="bright_red" if hit or state.player_hp <= 0 else "bright_green",
        height=spell_height,
        padding=(0, 1),
    )

    recent_logs = logs[-LOG_LINES:]
    log_content = Text(no_wrap=True, overflow="crop")
    if recent_logs:
        for index, log_line in enumerate(recent_logs):
            if index:
                log_content.append("\n")
            if "[FAIL]" in log_line or "마나가 부족하다" in log_line:
                style = "bold bright_red"
            elif "[WARN]" in log_line:
                style = "bold yellow"
            elif "[ OK ]" in log_line:
                style = "bold bright_green"
            else:
                style = "bright_green"
            log_content.append(log_line, style=style)
    else:
        log_content.append("전투 기록이 없습니다.", style="bright_green")
    log = Panel(
        log_content,
        title="[bold bright_green] BATTLE LOG | RECENT [/]",
        box=box.ASCII,
        border_style="bright_green",
        height=LOG_LINES + 2,
        padding=(0, 1),
    )
    prompt_lines = [
        Text(action_prompt, style="bold bright_green", justify="center",
             no_wrap=True, overflow="crop"),
    ]
    for row in cost_rows:
        prompt_lines.append(row)
    prompt_panel = Panel(
        Group(*prompt_lines),
        title="[bold bright_green] ACTION [/]",
        box=box.ASCII,
        border_style="bright_green",
        padding=(0, 1),
    )

    bottom = Table.grid(expand=True, padding=(0, 1))
    bottom.add_column(ratio=1, overflow="crop")
    bottom.add_column(ratio=2, overflow="crop")
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

    show(
        state,
        monster_art,
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
        known_spells=["fireball", "lightning", "shield", "heal"],
        experience=35,
        experience_to_next=60,
        level=3,
        monster_hp=20,
        monster_max_hp=80,
        shield=True,
        turn=4,
        stage=1,
        bonus_attack=10,
        bonus_heal=15,
        bonus_crit=0.15,
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
    show(
        test_state,
        test_art,
        logs=["[ OK ] PERMISSION GRANTED"],
        prompt="권한 상승 완료",
    )
