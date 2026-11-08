"""턴제 전투 로직. 화면 출력은 하지 않고 상태만 바꾸고 기록 문장을 돌려준다."""
from dataclasses import dataclass
import random
from typing import Optional

from battle.spells import SPELLS

PLAYER_MAX_HP = 100
MONSTER_MAX_HP = 80
MONSTER_ATTACK = 15
MONSTER_EMPOWERED_ATTACK = 20
LIGHTNING_CRITICAL_CHANCE = 0.4
LIGHTNING_CRITICAL_POWER = 50
TURN_PASS_LOG = "시간 초과(또는 발음 인식 실패)! 주문을 외우지 못해 플레이어 턴이 넘어갑니다."


@dataclass
class BattleState:
    monster_name: str = "슬라임"
    player_hp: int = PLAYER_MAX_HP
    player_max_hp: int = PLAYER_MAX_HP
    monster_hp: int = MONSTER_MAX_HP
    monster_max_hp: int = MONSTER_MAX_HP
    shield: bool = False      # True면 몬스터의 다음 공격을 막는다
    turn: int = 1
    monster_is_empowered: bool = False


def new_battle() -> BattleState:
    return BattleState()


def player_turn(state: BattleState, spell_key: Optional[str]) -> str:
    """플레이어가 주문을 쓴다. 전투 기록에 남길 문장을 돌려준다."""
    if spell_key in (None, "", "pass", "timeout") or spell_key not in SPELLS:
        return TURN_PASS_LOG

    spell = SPELLS[spell_key]
    if spell.kind == "attack":
        power = spell.power
        if spell_key == "lightning" and random.random() < LIGHTNING_CRITICAL_CHANCE:
            power = LIGHTNING_CRITICAL_POWER
            result = f"크리티컬 발동! {spell.display} 번개가 작렬해"
        else:
            result = f"{spell.display}!"
        state.monster_hp = max(0, state.monster_hp - power)
        return f"{result} {state.monster_name}에게 {power} 데미지"
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
    damage = MONSTER_EMPOWERED_ATTACK if state.monster_is_empowered else MONSTER_ATTACK
    attack_name = "강화 공격" if state.monster_is_empowered else "기본 공격"
    state.monster_is_empowered = not state.monster_is_empowered

    if state.shield:
        state.shield = False
        return f"{state.monster_name}의 {attack_name}! 실드가 공격을 완벽히 막아냈다 (0 데미지)"
    state.player_hp = max(0, state.player_hp - damage)
    return f"{state.monster_name}의 {attack_name}! {damage} 데미지를 입었다"


def winner(state: BattleState):
    """승자를 돌려준다: "player" / "monster" / 아직 진행 중이면 None"""
    if state.monster_hp <= 0:
        return "player"
    if state.player_hp <= 0:
        return "monster"
    return None


if __name__ == "__main__":
    # 단독 실행: python -m battle.engine
    from unittest.mock import patch

    state = new_battle()
    state.player_hp = 80
    print("[회복]", player_turn(state, "heal"))
    print("[시간 초과]", player_turn(state, "timeout"))
    print("[화염구]", player_turn(state, "fireball"))
    print("[몬스터]", monster_turn(state))
    print("[번개 크리티컬]")
    with patch("battle.engine.random.random", return_value=0.0):
        print(" ", player_turn(state, "lightning"))
    print("[몬스터]", monster_turn(state))
    print("[실드]", player_turn(state, "shield"))
    print("[몬스터]", monster_turn(state))
    print("[패스]", player_turn(state, "pass"))
    print("[몬스터]", monster_turn(state))
    print(f"플레이어 HP: {state.player_hp}/{state.player_max_hp}")
    print(f"몬스터 HP: {state.monster_hp}/{state.monster_max_hp}")
