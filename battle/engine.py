"""턴제 전투 로직. 화면 출력은 하지 않고 상태만 바꾸고 기록 문장을 돌려준다."""
from dataclasses import dataclass, field
import random
from typing import Optional

from battle.spells import SPELLS

PLAYER_MAX_HP = 100
PLAYER_MAX_MP = 50
MP_REGEN = 10  # 몬스터 턴마다 회복하는 마나
MONSTER_MAX_HP = 80
MONSTER_ATTACK = 15
MONSTER_EMPOWERED_ATTACK = 20
LIGHTNING_CRITICAL_CHANCE = 0.2
LIGHTNING_CRITICAL_POWER = 50
# 전투 기록은 시스템 로그 형식: [ OK ] 성공 / [WARN] 피해 / [FAIL] 실패 (docs/CONCEPT.md "화면 톤")
TURN_PASS_LOG = "[FAIL] 명령을 인식하지 못했습니다 (시간 초과 또는 발음 인식 실패). 턴이 넘어갑니다."
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
    monster_hp_rate: float = 1.0  # 몬스터 체력 배율 (시연용 빠른 모드에서 낮춘다)
    player_mp: int = PLAYER_MAX_MP
    player_max_mp: int = PLAYER_MAX_MP
    # 지금 쓸 수 있는 주문. 처음에는 starter 주문만, 나머지는 상점에서 배운다
    known_spells: list = field(default_factory=lambda: [k for k, s in SPELLS.items() if s.starter])
    monster_frozen: bool = False  # True면 몬스터의 다음 공격 1번을 건너뛴다 (ice)


def _scaled_hp(state: BattleState, hp: int) -> int:
    return max(1, round(hp * state.monster_hp_rate))


def new_battle(monster_hp_rate: float = 1.0) -> BattleState:
    """1스테이지부터 시작하는 새 전투. monster_hp_rate로 모든 몬스터 체력을 줄이거나 늘린다."""
    state = BattleState(monster_hp_rate=monster_hp_rate)
    name, hp, _, _ = STAGES[1]
    state.monster_name = name
    state.monster_hp = state.monster_max_hp = _scaled_hp(state, hp)
    return state


STAT_UPGRADES = {
    "1": "공격 패치 방 (주문 위력 +10)",
    "2": "백업 복구 방 (최대 체력 +20)",
    "3": "코어 오버클럭 방 (힐량 +15, 치명타율 +15%, 최대·현재 마나 +10)",
}
# 상점에서 배우는 주문의 고정 번호 (starter가 아닌 주문 순서대로 4부터)
SHOP_SPELL_NUMBERS = {str(4 + i): key for i, key in
                      enumerate(k for k, s in SPELLS.items() if not s.starter)}


def get_shop_options(state: BattleState) -> list[tuple[str, str]]:
    """상점(패키지 저장소) 선택지: [(입력할 번호, 설명)]. 1~3은 스탯 강화, 4부터는 아직 안 배운 주문.
    주문 번호는 배워도 바뀌지 않는다 (ice=4, meteor=5, focus=6, drain=7)."""
    options = list(STAT_UPGRADES.items())
    for number, key in SHOP_SPELL_NUMBERS.items():
        if key not in state.known_spells:
            spell = SPELLS[key]
            options.append((number, f"{key} 설치 (MP {spell.mana_cost}) - {spell.desc}"))
    return options


def get_upgrade_prompt() -> str:
    """다음 방의 스탯 업그레이드 선택지를 돌려준다."""
    return "몬스터 처치! 다음 방을 선택하세요: " + "  ".join(
        f"[{key}] {label}" for key, label in STAT_UPGRADES.items())


def advance_stage(state: BattleState) -> None:
    """다음 단계 몬스터로 상태를 갱신한다."""
    if state.stage >= max(STAGES):
        raise ValueError("마지막 스테이지 이후로는 진행할 수 없습니다.")
    state.stage += 1
    name, hp, _, _ = STAGES[state.stage]
    state.monster_name = name
    state.monster_hp = state.monster_max_hp = _scaled_hp(state, hp)
    state.monster_is_empowered = False
    state.monster_frozen = False
    state.shield = False
    state.awaiting_upgrade = False


def apply_upgrade(state: BattleState, choice: str) -> str:
    """선택한 업그레이드를 적용하고 다음 단계로 이동한다."""
    if not state.awaiting_upgrade:
        raise ValueError("몬스터 처치 후에만 업그레이드를 선택할 수 있습니다.")

    normalized = choice.strip().lower()
    if normalized in ("1", "attack", "공격력"):
        state.bonus_attack += 10
        result = "공격 패치 방 적용: 주문 위력 +10"
    elif normalized in ("2", "hp", "체력"):
        state.player_max_hp += 20
        state.player_hp += 20
        result = "백업 복구 방 적용: 최대·현재 체력 +20"
    elif normalized in ("3", "magic", "마력"):
        state.bonus_heal += 15
        previous_crit = state.bonus_crit
        state.bonus_crit = min(1.0, state.bonus_crit + 0.15)
        crit_gain = round((state.bonus_crit - previous_crit) * 100)
        state.player_max_mp += 10
        state.player_mp += 10
        result = (f"코어 오버클럭 방 적용: 힐량 +15, 치명타율 +{crit_gain}%, "
                  "최대·현재 마나 +10")
    else:
        # 4번부터는 상점에서 주문 배우기. 번호 대신 주문 이름을 넣어도 된다
        key = SHOP_SPELL_NUMBERS.get(normalized, normalized)
        if key not in SPELLS or key in state.known_spells:
            raise ValueError(f"알 수 없는 업그레이드 선택: {choice}")
        state.known_spells.append(key)
        result = f"{key} 명령을 설치했습니다 (MP {SPELLS[key].mana_cost})."

    advance_stage(state)
    return f"[ OK ] 다음 방 강화 완료: {result} 다음 스테이지({state.stage})로 이동합니다."


def _hit_monster(state: BattleState, power: int) -> None:
    """몬스터 체력을 깎는다. 중간 스테이지 몬스터를 쓰러뜨리면 상점(업그레이드)을 기다리는 상태가 된다."""
    state.monster_hp = max(0, state.monster_hp - power)
    if state.monster_hp == 0 and state.stage < max(STAGES):
        state.awaiting_upgrade = True


def player_turn(state: BattleState, spell_key: Optional[str]) -> str:
    """플레이어가 주문을 쓴다. 전투 기록에 남길 문장을 돌려준다."""
    if spell_key in (None, "", "pass", "timeout") or spell_key not in SPELLS:
        return TURN_PASS_LOG

    spell = SPELLS[spell_key]
    if spell_key not in state.known_spells:
        return f"[FAIL] {spell_key} 명령이 설치되어 있지 않습니다. 상점에서 배울 수 있어요. 턴이 넘어갑니다."
    if state.player_mp < spell.mana_cost:
        return (f"[FAIL] 마나가 부족하다: {spell_key}에 MP {spell.mana_cost} 필요 "
                f"(현재 {state.player_mp}). 턴이 넘어갑니다.")
    state.player_mp -= spell.mana_cost

    if spell.kind == "attack":
        power = spell.power + state.bonus_attack
        critical_chance = min(1.0, LIGHTNING_CRITICAL_CHANCE + state.bonus_crit)
        if spell_key == "lightning" and random.random() < critical_chance:
            power = LIGHTNING_CRITICAL_POWER + state.bonus_attack
            result = f"[ OK ] {spell.key} 크리티컬! 과전압으로"
        else:
            result = f"[ OK ] {spell.key} 실행:"
        _hit_monster(state, power)
        return f"{result} {state.monster_name}에게 {power} 데미지"
    if spell.kind == "freeze":
        power = spell.power + state.bonus_attack
        _hit_monster(state, power)
        state.monster_frozen = True
        return f"[ OK ] {spell.key} 실행: 프로세스 일시정지, {state.monster_name}에게 {power} 데미지"
    if spell.kind == "drain":
        power = spell.power + state.bonus_attack
        dealt = min(power, state.monster_hp)
        _hit_monster(state, power)
        before = state.player_hp
        state.player_hp = min(state.player_max_hp, state.player_hp + dealt)
        return (f"[ OK ] {spell.key} 실행: 리소스 훔치기, {state.monster_name}에게 {power} 데미지, "
                f"체력 {state.player_hp - before} 회복")
    if spell.kind == "mana":
        before = state.player_mp
        state.player_mp = min(state.player_max_mp, state.player_mp + spell.power)
        return f"[ OK ] {spell.key} 실행: 캐시 비우기, 마나 {state.player_mp - before} 회복"
    if spell.kind == "heal":
        before = state.player_hp
        state.player_hp = min(
            state.player_max_hp, state.player_hp + spell.power + state.bonus_heal
        )
        return f"[ OK ] {spell.key} 실행: 시스템 복구, 체력 {state.player_hp - before} 회복"
    if spell.kind == "shield":
        state.shield = True
        return f"[ OK ] {spell.key} 실행: 방화벽 가동, 다음 공격을 막는다"
    raise ValueError(f"알 수 없는 주문 종류: {spell.kind}")


def monster_turn(state: BattleState) -> str:
    """몬스터가 반격한다. 전투 기록에 남길 문장을 돌려준다."""
    state.turn += 1
    state.player_mp = min(state.player_max_mp, state.player_mp + MP_REGEN)
    if state.monster_frozen:
        state.monster_frozen = False
        return f"[ OK ] 프로세스 일시정지: {state.monster_name}의 공격이 멈췄다 (0 데미지)"
    _, _, base_attack, empowered_attack = STAGES[state.stage]
    damage = empowered_attack if state.monster_is_empowered else base_attack
    attack_name = "강화 공격" if state.monster_is_empowered else "기본 공격"
    state.monster_is_empowered = not state.monster_is_empowered

    if state.shield:
        state.shield = False
        return f"[ OK ] 방화벽이 {state.monster_name}의 {attack_name}을 막았다 (0 데미지)"
    state.player_hp = max(0, state.player_hp - damage)
    return f"[WARN] {state.monster_name}의 {attack_name}: {damage} 데미지"


def room_event(state: BattleState, kind: str) -> str:
    """던전에서 전투가 아닌 방에 들어갔을 때의 효과. 상태를 바꾸고 기록 문장을 돌려준다.
    kind: "spring"(백업 파일) / "treasure"(패치 파일)."""
    if kind == "spring":
        state.player_hp = min(state.player_hp + 40, state.player_max_hp)
        state.player_mp = min(state.player_mp + 30, state.player_max_mp)
        return (
            f"[ OK ] 백업 파일 복원: 체력 +40, 마나 +30 복구 완료 "
            f"(현재 HP: {state.player_hp}/{state.player_max_hp}, "
            f"MP: {state.player_mp}/{state.player_max_mp})"
        )
    if kind == "treasure":
        state.bonus_attack += 10
        state.player_max_mp += 15
        state.player_mp += 15
        state.bonus_crit = min(1.0, state.bonus_crit + 0.10)
        return "[ PATCH ] 패치 파일 적용: 주문 위력 +10, 최대 마나 +15, 치명타율 +10% 강화 완료"
    raise ValueError(f"효과가 없는 방 종류: {kind}")


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
            state.player_mp = state.player_max_mp  # 이 검증은 공격력·스테이지 확인용이라 마나는 매번 채운다
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

    # 마나와 상점(패키지 저장소) 확인
    shop = new_battle()
    assert shop.player_mp == PLAYER_MAX_MP and "ice" not in shop.known_spells
    assert "설치되어 있지 않습니다" in player_turn(shop, "ice")
    shop.player_mp = 5
    assert "마나가 부족하다" in player_turn(shop, "fireball") and shop.player_mp == 5
    print("[마나 확인] 안 배운 주문과 마나 부족은 실패하고 턴만 넘어감")

    shop.player_mp = 0
    monster_turn(shop)
    assert shop.player_mp == MP_REGEN
    print(f"[마나 회복 확인] 몬스터 턴마다 마나 +{MP_REGEN}")

    shop.awaiting_upgrade = True
    options = get_shop_options(shop)
    print("[상점 선택지]", options)
    assert [key for key, _ in options] == ["1", "2", "3", "4", "5", "6", "7"]
    print(apply_upgrade(shop, "4"))
    assert shop.known_spells[-1] == "ice" and shop.stage == 2

    shop.player_mp, shop.monster_hp = 50, 80
    print("[ice]", player_turn(shop, "ice"))
    assert shop.monster_frozen and shop.player_mp == 35
    hp_before = shop.player_hp
    print("[ice 다음 몬스터 턴]", monster_turn(shop))
    assert shop.player_hp == hp_before and not shop.monster_frozen

    for key in ("meteor", "focus"):
        shop.awaiting_upgrade = True
        print(apply_upgrade(shop, key))
    assert shop.stage == 4 and "meteor" in shop.known_spells and "focus" in shop.known_spells
    shop.known_spells.append("drain")  # 마지막 스테이지 뒤에는 상점이 없어서 검증용으로 직접 추가

    shop.player_mp, shop.player_hp = 10, 50
    print("[focus]", player_turn(shop, "focus"))
    assert shop.player_mp == 30
    print("[drain]", player_turn(shop, "drain"))
    assert shop.player_hp == 65 and shop.player_mp == 10
    shop.player_mp = 30
    meteor_log = player_turn(shop, "meteor")
    print("[meteor]", meteor_log)
    assert "45 데미지" in meteor_log and shop.player_mp == 0
    print("[주문 상점 확인] ice, meteor, focus, drain 설치와 효과 정상")

    # 던전 방 효과
    room = new_battle()
    room.player_hp, room.player_mp = 50, 10
    spring_log = room_event(room, "spring")
    print("[백업 파일]", spring_log)
    assert room.player_hp == 90 and room.player_mp == 40
    assert spring_log == (
        "[ OK ] 백업 파일 복원: 체력 +40, 마나 +30 복구 완료 "
        "(현재 HP: 90/100, MP: 40/50)"
    )

    capped_spring_state = new_battle()
    capped_spring_state.player_hp, capped_spring_state.player_mp = 90, 45
    capped_spring_log = room_event(capped_spring_state, "spring")
    print("[백업 파일 상한 확인]", capped_spring_log)
    assert capped_spring_state.player_hp == 100 and capped_spring_state.player_mp == 50

    patch_state = new_battle()
    patch_state.player_mp = 20
    patch_log = room_event(patch_state, "treasure")
    print("[패치 파일]", patch_log)
    assert patch_state.bonus_attack == 10
    assert patch_state.player_max_mp == 65 and patch_state.player_mp == 35
    assert patch_state.bonus_crit == 0.1
    assert patch_log == (
        "[ PATCH ] 패치 파일 적용: 주문 위력 +10, 최대 마나 +15, "
        "치명타율 +10% 강화 완료"
    )

    capped_patch_state = new_battle()
    capped_patch_state.bonus_crit = 0.95
    room_event(capped_patch_state, "treasure")
    assert capped_patch_state.bonus_crit == 1.0
    print("[던전 방 확인] 백업 파일 회복량 clamp, 패치 파일 영구 강화 및 치명타 상한 정상")
