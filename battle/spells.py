"""주문 목록. 주문을 추가하려면 SPELLS에 한 줄을 넣으면 된다."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Spell:
    key: str              # 내부 이름 (다른 모듈과 주고받는 값)
    display: str          # 화면에 큰 글씨로 보여 줄 이름 (영어만 가능)
    kind: str             # "attack" / "shield" / "heal" / "freeze" / "mana" / "drain"
    power: int            # attack·freeze·drain: 데미지, heal: 회복량, mana: 마나 회복량, shield: 사용 안 함
    phrases: tuple[str, ...]  # 음성으로 인식할 말 (모델 어휘에 있는 영어 단어)
    mana_cost: int = 0    # 쓸 때 드는 마나 (MP)
    starter: bool = True  # True면 처음부터 쓸 수 있고, False면 상점(패키지 저장소)에서 배워야 한다
    desc: str = ""        # 주문 목록·상점에 보여 줄 짧은 설명 (docs/CONCEPT.md의 주문 의미)


SPELLS = {
    "fireball": Spell("fireball", "FIREBALL", "attack", 25, ("fireball", "fire ball", "fire"),
                      10, True, "프로세스 강제 종료: 25 데미지"),
    "lightning": Spell("lightning", "LIGHTNING", "attack", 15, ("lightning", "lightening", "thunder"),
                       15, True, "과전압: 15 데미지, 20% 확률로 크리티컬 50"),
    "shield": Spell("shield", "SHIELD", "shield", 0, ("shield", "protect", "defend"),
                    5, True, "방화벽: 다음 공격을 막음"),
    # health는 일상 단어라 오인식이 잦아 뺐다. cure는 문서와 안내문에 있어 유지
    "heal": Spell("heal", "HEAL", "heal", 30, ("heal", "cure"),
                  15, True, "시스템 복구: 체력 30 회복"),
    # 아래는 상점에서 배우는 주문
    "ice": Spell("ice", "ICE", "freeze", 10, ("ice", "freeze", "frost"),
                 15, False, "프로세스 일시정지: 10 데미지 + 몬스터 다음 공격 1번 멈춤"),
    "meteor": Spell("meteor", "METEOR", "attack", 45, ("meteor",),
                    30, False, "디스크 포맷: 45 데미지"),
    "focus": Spell("focus", "FOCUS", "mana", 20, ("focus", "meditate"),
                   0, False, "캐시 비우기: 마나 20 회복"),
    "drain": Spell("drain", "DRAIN", "drain", 15, ("drain",),
                   20, False, "리소스 훔치기: 15 데미지, 그만큼 체력 회복"),
}
