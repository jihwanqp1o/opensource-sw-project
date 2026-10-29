"""rich로 전투 화면을 그린다. 게임 로직은 모르고, 받은 값만 보여 준다."""
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

console = Console()


def _hp_bar(label, hp, max_hp, color):
    row = Table.grid(padding=(0, 1))
    row.add_row(Text(label, style="bold"), ProgressBar(total=max_hp, completed=hp, width=20,
                                                       complete_style=color), f"{hp}/{max_hp}")
    return row


def render(state, monster_art, banner=None, logs=(), hit=False, prompt=""):
    """화면 한 장을 만든다. hit=True면 몬스터가 피격 색으로 보인다."""
    monster = Panel(Text(monster_art, style="bold red" if hit else "green"),
                    title=state.monster_name, border_style="red" if hit else "white")

    status = Panel(Group(
        _hp_bar("플레이어", state.player_hp, state.player_max_hp, "cyan"),
        _hp_bar("몬스터  ", state.monster_hp, state.monster_max_hp, "red"),
        Text(""),
        Text(f"턴 {state.turn}    실드: {'ON' if state.shield else 'OFF'}"),
    ), title="상태")

    top = Table.grid(expand=True)
    top.add_column(ratio=1)
    top.add_column(ratio=1)
    top.add_row(monster, status)

    spell = Panel(Text(banner or "", style="bold yellow"), title="주문", height=8)
    log = Panel(Text("\n".join(list(logs)[-5:])), title="전투 기록", height=7)
    return Group(top, spell, log, Text(prompt, style="bold"))


def show(*args, **kwargs):
    """화면을 지우고 새로 그린다. 인자는 render()와 같다."""
    console.clear()
    console.print(render(*args, **kwargs))


if __name__ == "__main__":
    # 단독 실행: python -m ui.screen  (가짜 값으로 화면 모양만 확인)
    from types import SimpleNamespace

    fake = SimpleNamespace(monster_name="슬라임", player_hp=70, player_max_hp=100,
                           monster_hp=40, monster_max_hp=100, shield=True, turn=3)
    show(fake, "  (o_o)\n  /| |\\", banner="  FIREBALL", logs=["FIREBALL! 20 데미지"],
         hit=True, prompt="주문을 외치세요: fireball / shield / heal")
