"""턴제 전투 로직. 화면 출력은 하지 않고 상태만 바꾸고 기록 문장을 돌려준다."""
from dataclasses import dataclass
import random
from typing import Optional

from battle.spells import SPELLS

PLAYER_MAX_HP = 100
MONSTER_MAX_HP = 80
MONSTER_ATTACK = 15
MONSTER_EMPOWERED_ATTACK = 20
LIGHTNING_CRITICAL_CHANCE = 0.2
LIGHTNING_CRITICAL_POWER = 50
TURN_PASS_LOG = "시간 초과(또는 발음 인식 실패)! 주문을 외우지 못해 플레이어 턴이 넘어갑니다."
# 스테이지: (몬스터 이름, 체력, 기본 공격, 강화 공격). 이름은 docs/CONCEPT.md의 오류 생물 이름을 따른다.
STAGES = {
    1: ("메모리 누수 슬라임", 80, 15, 20),
    2: ("버그 고블린", 80, 15, 20),
    3: ("좀비 프로세스", 120, 15, 20),
    4: ("커널 패닉 드래곤", 200, 20, 25),
}


@dataclass
class BattleState:
    monster_name: str = STAGES[1][0]
    player_hp: int = PLAYER_MAX_HP
    player_max_hp: int = PLAYER_MAX_HP
    monster_hp: int = MONSTER_MAX_HP
    monster_max_hp: int = MONSTER_MAX_HP
    shield: bool = False      # True면 몬스터의 다음 공격을 막는다
    turn: int = 1
    monster_is_empowered: bool = False
    bonus_attack: int = 0
    bonus_heal: int = 0
    bonus_crit: float = 0.0
    stage: int = 1
    awaiting_upgrade: bool = False


def new_battle() -> BattleState:
    name, hp, _, _ = STAGES[1]
    return BattleState(monster_name=name, monster_hp=hp, monster_max_hp=hp)


def get_upgrade_prompt() -> str:
    """업그레이드 선택지를 한국어로 돌려준다."""
    return (
        "몬스터 처치! 강화할 스탯을 선택하세요: "
        "[1] 공격력 (+10)  [2] 체력 (+20)  "
        "[3] 마력 (힐량 +15, 크리티컬 확률 +15%)"
    )


def advance_stage(state: BattleState) -> None:
    """다음 단계 몬스터로 상태를 갱신한다."""
    if state.stage >= max(STAGES):
        raise ValueError("마지막 스테이지 이후로는 진행할 수 없습니다.")
    state.stage += 1
    name, hp, _, _ = STAGES[state.stage]
    state.monster_name = name
    state.monster_hp = hp
    state.monster_max_hp = hp
    state.monster_is_empowered = False
    state.shield = False
    state.awaiting_upgrade = False


def apply_upgrade(state: BattleState, choice: str) -> str:
    """선택한 업그레이드를 적용하고 다음 단계로 이동한다."""
    if not state.awaiting_upgrade:
        raise ValueError("몬스터 처치 후에만 업그레이드를 선택할 수 있습니다.")

    normalized = choice.strip().lower()
    if normalized in ("1", "attack", "공격력"):
        state.bonus_attack += 10
        result = "공격력이 +10 상승했습니다."
    elif normalized in ("2", "hp", "체력"):
        state.player_max_hp += 20
        state.player_hp += 20
        result = "최대 체력과 현재 체력이 각각 +20 상승했습니다."
    elif normalized in ("3", "magic", "마력"):
        state.bonus_heal += 15
        previous_crit = state.bonus_crit
        state.bonus_crit = min(1.0, state.bonus_crit + 0.15)
        crit_gain = round((state.bonus_crit - previous_crit) * 100)
        result = f"힐량이 +15, 크리티컬 확률이 +{crit_gain}% 상승했습니다."
    else:
        raise ValueError(f"알 수 없는 업그레이드 선택: {choice}")

    advance_stage(state)
    return f"[업그레이드 완료] {result} 다음 스테이지({state.stage})로 이동합니다."


def player_turn(state: BattleState, spell_key: Optional[str]) -> str:
    """플레이어가 주문을 쓴다. 전투 기록에 남길 문장을 돌려준다."""
    if spell_key in (None, "", "pass", "timeout") or spell_key not in SPELLS:
        return TURN_PASS_LOG

    spell = SPELLS[spell_key]
    if spell.kind == "attack":
        power = spell.power + state.bonus_attack
        critical_chance = min(1.0, LIGHTNING_CRITICAL_CHANCE + state.bonus_crit)
        if spell_key == "lightning" and random.random() < critical_chance:
            power = LIGHTNING_CRITICAL_POWER + state.bonus_attack
            result = f"크리티컬 발동! {spell.display} 번개가 작렬해"
        else:
            result = f"{spell.display}!"
        state.monster_hp = max(0, state.monster_hp - power)
        if state.monster_hp == 0 and state.stage < max(STAGES):
            state.awaiting_upgrade = True
        return f"{result} {state.monster_name}에게 {power} 데미지"
    if spell.kind == "heal":
        before = state.player_hp
        state.player_hp = min(
            state.player_max_hp, state.player_hp + spell.power + state.bonus_heal
        )
        return f"{spell.display}! 체력 {state.player_hp - before} 회복"
    if spell.kind == "shield":
        state.shield = True
        return f"{spell.display}! 다음 공격을 막을 준비를 했다"
    raise ValueError(f"알 수 없는 주문 종류: {spell.kind}")


def monster_turn(state: BattleState) -> str:
    """몬스터가 반격한다. 전투 기록에 남길 문장을 돌려준다."""
    state.turn += 1
    _, _, base_attack, empowered_attack = STAGES[state.stage]
    damage = empowered_attack if state.monster_is_empowered else base_attack
    attack_name = "강화 공격" if state.monster_is_empowered else "기본 공격"
    state.monster_is_empowered = not state.monster_is_empowered

    if state.shield:
        state.shield = False
        return f"{state.monster_name}의 {attack_name}! 실드가 공격을 완벽히 막아냈다 (0 데미지)"
    state.player_hp = max(0, state.player_hp - damage)
    return f"{state.monster_name}의 {attack_name}! {damage} 데미지를 입었다"


def winner(state: BattleState):
    """승자를 돌려준다: "player"(마지막 스테이지 처치) / "monster" / 아직 진행 중이면 None.
    상태를 바꾸지 않는다. 중간 스테이지 처치는 state.awaiting_upgrade로 알 수 있다 (player_turn이 설정)."""
    if state.monster_hp <= 0:
        return "player" if state.stage == max(STAGES) else None
    if state.player_hp <= 0:
        return "monster"
    return None


if __name__ == "__main__":
    # 단독 실행: python -m battle.engine
    from unittest.mock import patch

    assert SPELLS["heal"].power == 30
    assert "health" not in SPELLS["heal"].phrases
    assert LIGHTNING_CRITICAL_CHANCE == 0.2
    print("[밸런스 확인] 힐 30, 번개 기본 위력 15/크리티컬 위력 50, 크리티컬 확률 20%")
    print(f"[힐 인식 phrases] {SPELLS['heal'].phrases} (health 제외)")

    balance_state = new_battle()
    balance_state.player_hp = 50
    print("[힐 테스트]", player_turn(balance_state, "heal"))
    assert balance_state.player_hp == 80
    with patch("battle.engine.random.random", return_value=0.2):
        normal_log = player_turn(balance_state, "lightning")
    assert "크리티컬" not in normal_log
    with patch("battle.engine.random.random", return_value=0.199):
        critical_log = player_turn(balance_state, "lightning")
    assert "크리티컬" in critical_log
    assert "50 데미지" in critical_log
    print("[번개 확률 경계 확인] 0.20은 일반 공격, 0.199는 크리티컬")
    print("[번개 크리티컬 테스트]", critical_log)

    state = new_battle()

    def defeat_current_stage():
        print(f"\n[스테이지 {state.stage}] {state.monster_name} 등장 (HP {state.monster_hp})")
        while state.monster_hp > 0:
            print(" ", player_turn(state, "fireball"))
        result = winner(state)
        if state.stage < max(STAGES):
            assert result is None and state.awaiting_upgrade
        else:
            assert result == "player"
        print(
            f"[스테이지 {state.stage} 처치] 몬스터 HP {state.monster_hp}/"
            f"{state.monster_max_hp}, 업그레이드 대기: {state.awaiting_upgrade}"
        )

    def choose_upgrade(choice):
        print(get_upgrade_prompt())
        print(apply_upgrade(state, choice))
        print(
            f"[누적 스탯] 공격력 +{state.bonus_attack}, 힐량 +{state.bonus_heal}, "
            f"크리티컬 확률 +{state.bonus_crit:.0%}, "
            f"플레이어 HP {state.player_hp}/{state.player_max_hp}"
        )

    defeat_current_stage()
    assert state.awaiting_upgrade
    choose_upgrade("1")
    assert state.bonus_attack == 10

    defeat_current_stage()
    assert state.awaiting_upgrade
    choose_upgrade("2")
    assert state.player_max_hp == 120 and state.player_hp == 120

    defeat_current_stage()
    assert state.awaiting_upgrade
    choose_upgrade("3")
    assert state.bonus_heal == 15 and state.bonus_crit == 0.15
    assert state.stage == 4 and state.monster_max_hp == 200

    upgraded_heal_state = new_battle()
    upgraded_heal_state.player_hp = 50
    upgraded_heal_state.bonus_heal = state.bonus_heal
    upgraded_heal_log = player_turn(upgraded_heal_state, "heal")
    assert upgraded_heal_state.player_hp == 95
    print("[마력 업그레이드 힐 확인]", upgraded_heal_log)

    capped_state = new_battle()
    capped_state.awaiting_upgrade = True
    capped_state.bonus_crit = 0.95
    apply_upgrade(capped_state, "magic")
    assert capped_state.bonus_crit == 1.0
    print("[크리티컬 상한 확인] 업그레이드 누적 확률은 100%를 넘지 않음")

    print(
        f"\n[스테이지 4 확인] {state.monster_name}, 몬스터 HP "
        f"{state.monster_hp}/{state.monster_max_hp}"
    )
    assert state.player_hp == 120
    print("[스테이지 4 공격 확인]", monster_turn(state))
    print("[스테이지 4 공격 확인]", monster_turn(state))
    assert state.player_hp == 75

    critical_state = new_battle()
    critical_state.bonus_attack = state.bonus_attack
    critical_state.bonus_crit = state.bonus_crit
    with patch("battle.engine.random.random", return_value=0.0):
        upgraded_critical_log = player_turn(critical_state, "lightning")
    assert "60 데미지" in upgraded_critical_log
    print("[업그레이드 번개 크리티컬 확인]", upgraded_critical_log)

    defeat_current_stage()
    assert winner(state) == "player"
    print(
        f"\n[최종 승리] {state.stage}스테이지 완료, "
        f"공격력 +{state.bonus_attack}, 힐량 +{state.bonus_heal}, "
        f"크리티컬 확률 +{state.bonus_crit:.0%}"
    )
