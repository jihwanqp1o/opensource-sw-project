"""턴제 전투 로직. 화면 출력은 하지 않고 상태만 바꾸고 기록 문장을 돌려준다."""
from dataclasses import dataclass

from battle.spells import SPELLS

PLAYER_MAX_HP = 100
MONSTER_MAX_HP = 100
MONSTER_ATTACK = 15


@dataclass
class BattleState:
    monster_name: str = "슬라임"
    player_hp: int = PLAYER_MAX_HP
    player_max_hp: int = PLAYER_MAX_HP
    monster_hp: int = MONSTER_MAX_HP
    monster_max_hp: int = MONSTER_MAX_HP
    shield: bool = False      # True면 몬스터의 다음 공격을 막는다
    turn: int = 1


def new_battle() -> BattleState:
    return BattleState()


def player_turn(state: BattleState, spell_key: str) -> str:
    """플레이어가 주문을 쓴다. 전투 기록에 남길 문장을 돌려준다."""
    spell = SPELLS[spell_key]
    if spell.kind == "attack":
        state.monster_hp = max(0, state.monster_hp - spell.power)
        return f"{spell.display}! {state.monster_name}에게 {spell.power} 데미지"
    if spell.kind == "heal":
        before = state.player_hp
        state.player_hp = min(state.player_max_hp, state.player_hp + spell.power)
        return f"{spell.display}! 체력 {state.player_hp - before} 회복"
    if spell.kind == "shield":
        state.shield = True
        return f"{spell.display}! 다음 공격을 막을 준비를 했다"
    raise ValueError(f"알 수 없는 주문 종류: {spell.kind}")


def monster_turn(state: BattleState) -> str:
    """몬스터가 반격한다. 전투 기록에 남길 문장을 돌려준다."""
    state.turn += 1
    if state.shield:
        state.shield = False
        return f"{state.monster_name}의 공격! 실드가 막아냈다"
    state.player_hp = max(0, state.player_hp - MONSTER_ATTACK)
    return f"{state.monster_name}의 공격! {MONSTER_ATTACK} 데미지를 입었다"


def winner(state: BattleState):
    """승자를 돌려준다: "player" / "monster" / 아직 진행 중이면 None"""
    if state.monster_hp <= 0:
        return "player"
    if state.player_hp <= 0:
        return "monster"
    return None


if __name__ == "__main__":
    # 단독 실행: python -m battle.engine
    s = new_battle()
    for key in ["fireball", "shield", "fireball", "heal", "fireball", "fireball", "fireball"]:
        print(f"[턴 {s.turn}]", player_turn(s, key))
        if winner(s):
            break
        print("        ", monster_turn(s))
        print(f"         플레이어 {s.player_hp} / 몬스터 {s.monster_hp}")
    print("승자:", winner(s))
