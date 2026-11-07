"""Rich를 사용해 턴제 전투 화면을 그린다."""
import time

from rich.console import Console, Group
from rich import box
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

console = Console(force_terminal=True)


def _get_hp_color(current, maximum):
    """체력 비율에 따른 진행 바 색상을 돌려준다."""
    if maximum <= 0:
        return "bright_red"

    rate = current / maximum
    if rate >= 0.7:
        return "cyan"
    if rate < 0.3:
        return "red"
    return "bright_black"


def _hp_bar(label, hp, max_hp):
    """체력 수치와 진행 바를 한 줄로 만든다."""
    color = _get_hp_color(hp, max_hp)
    total = max(max_hp, 1)
    completed = max(0, min(hp, total))
    displayed_max = max(max_hp, 0)

    row = Table.grid(padding=(0, 1))
    row.add_column(no_wrap=True)
    row.add_column()
    row.add_column(justify="right", no_wrap=True)
    row.add_row(
        Text(label, style="bold white"),
        ProgressBar(total=total, completed=completed, width=14,
                    complete_style=color, finished_style=color),
        Text(f"{hp}/{displayed_max}", style=f"bold {color}"),
    )
    return row


def render(state, monster_art, banner=None, logs=(), hit=False, prompt=""):
    """전투 상태를 Rich 렌더러블로 만든다."""
    monster = Panel(
        Text(monster_art, style="bold red" if hit else "white",
             justify="center"),
        title=f"[bold white] {state.monster_name} [/]",
        subtitle="[bold red]HIT![/]" if hit else "[dim]ENEMY[/]",
        box=box.ROUNDED,
        border_style="bold red" if hit else "bright_black",
        padding=(1, 2),
    )

    shield_badge = (
        Text(" SHIELD ACTIVE ", style="bold white on bright_black")
        if state.shield
        else Text(" SHIELD OFF ", style="dim")
    )
    hp_row = Table.grid(expand=True, padding=(0, 2))
    hp_row.add_column(ratio=1)
    hp_row.add_column(ratio=1)
    hp_row.add_row(
        _hp_bar("PLAYER", state.player_hp, state.player_max_hp),
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
        padding=(0, 2),
    )

    spell_text = Text(banner or "주문을 기다리는 중...", justify="center")
    if banner:
        spell_text.stylize("bold red" if hit else "bold white")
    else:
        spell_text.stylize("dim")
    spell = Panel(
        spell_text,
        title="[bold white] SPELL · 주문 발동 [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        padding=(1, 2),
    )

    recent_logs = list(logs)[-5:]
    log_content = Text("\n".join(recent_logs) if recent_logs else "전투 기록이 없습니다.",
                       style="white")
    log = Panel(
        log_content,
        title="[bold white] BATTLE LOG · 최근 기록 [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        height=8,
        padding=(0, 1),
    )
    prompt_content = Text(prompt or "입력 대기 중...", style="bold white",
                          justify="center")
    prompt_panel = Panel(
        prompt_content,
        title="[bold white] ACTION [/]",
        box=box.ROUNDED,
        border_style="bright_black",
        height=8,
        padding=(1, 1),
    )

    bottom = Table.grid(expand=True, padding=(0, 1))
    bottom.add_column(ratio=2)
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
    return f"💥\n{monster_art}\n💥"


def play_turn_sequence(state, spell_name, player_dmg, monster_dmg,
                       monster_art=None, logs=None, prompt=""):
    """주문 영창부터 피격, 몬스터 반격까지 순서대로 연출한다."""
    if logs is None:
        logs = []
    if monster_art is None:
        monster_art = "      .---.\n     ( o o )\n      \\___/"

    # 1. 주문 영창 연출
    for dots in (".", "..", "..."):
        casting_banner = f"✦ [{spell_name}] 마나 응축 중{dots}"
        show(state, monster_art, banner=casting_banner, logs=logs,
             prompt="마법 집중...")
        time.sleep(0.35)

    # 2. 파이어볼 비행 연출
    projectile_frames = (
        f"( > ) > >  🔥 {spell_name}",
        "      ( >> ) >> 🔥 >>>",
        "            ( >>> ) 🔥 💥",
    )
    for frame in projectile_frames:
        show(state, monster_art, banner=frame, logs=logs,
             prompt="주문 발사!")
        time.sleep(0.12)

    # 3. 몬스터 피격 및 폭발 연출
    state.monster_hp = max(0, state.monster_hp - player_dmg)
    logs.append(f"{spell_name} 명중! {player_dmg} 데미지")
    hit_art = _hit_monster_art(monster_art)
    explosion_frames = (
        ". : * 💥 IMPACT 💥 * : .",
        "( ° ﾟ º  🔥 BOOM! 🔥  º ﾟ ° )",
        "·  '  .  *  ✦  *  .  '  ·",
    )

    for frame, hit in zip(explosion_frames, (True, False, True)):
        explosion_banner = f"{frame}\n- {player_dmg} DAMAGE -"
        show(state, hit_art if hit else monster_art,
             banner=explosion_banner, logs=logs, hit=hit,
             prompt="타격 성공!")
        time.sleep(0.1)

    # 4. 반격 또는 승리 연출
    if state.monster_hp > 0:
        state.player_hp = max(0, state.player_hp - monster_dmg)
        logs.append(
            f"{state.monster_name}의 반격! 플레이어가 {monster_dmg} 데미지를 입었다"
        )
        counter_banner = (
            f"⚠ WARNING: {state.monster_name.upper()} COUNTERATTACK ⚠\n"
            f"- {monster_dmg} DAMAGE TO PLAYER -"
        )
        show(state, monster_art, banner=counter_banner, logs=logs,
             prompt="반격!")
        time.sleep(0.8)
    else:
        logs.append("승리! 몬스터를 쓰러뜨렸다.")
        show(state, monster_art, banner="✦ ✦ VICTORY! ✦ ✦",
             logs=logs, prompt="전투 승리!")


if __name__ == "__main__":
    from types import SimpleNamespace

    test_state = SimpleNamespace(
        monster_name="화염 슬라임",
        player_hp=72,
        player_max_hp=100,
        monster_hp=50,
        monster_max_hp=80,
        shield=True,
        turn=3,
    )
    test_art = "      .---.\n     ( o o )\n      \\___/"
    test_logs = [
        "전투가 시작되었습니다.",
        "슬라임이 노려보고 있습니다.",
    ]

    show(
        test_state,
        test_art,
        logs=test_logs,
        prompt="AWAITING SPELL: fireball / shield / heal",
    )