"""주문 목록. 주문을 추가하려면 SPELLS에 한 줄을 넣으면 된다."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Spell:
    key: str              # 내부 이름 (다른 모듈과 주고받는 값)
    display: str          # 화면에 큰 글씨로 보여 줄 이름 (영어만 가능)
    kind: str             # "attack" / "shield" / "heal"
    power: int            # attack: 데미지, heal: 회복량, shield: 사용 안 함
    phrases: tuple        # 음성으로 인식할 말 (모델 어휘에 있는 영어 단어)


SPELLS = {
    "fireball": Spell("fireball", "FIREBALL", "attack", 20, ("fireball", "fire ball", "fire")),
    "shield": Spell("shield", "SHIELD", "shield", 0, ("shield",)),
    "heal": Spell("heal", "HEAL", "heal", 15, ("heal",)),
}
