"""던전 지도: 방과 갈림길 연결만 정한다. 화면 출력과 전투 계산은 하지 않는다. (담당: 지환)

세계관상 던전은 디렉터리 트리이고, 갈림길에서 방향을 외치는 것은 cd 할 폴더를 고르는 것이다 (docs/CONCEPT.md).
몬스터 방은 어느 길로 가도 1 → 2 → 3 → 4스테이지 순서로 나온다 (battle.engine.STAGES와 맞춤).
"""
from dataclasses import dataclass, field

# 방 종류: monster(전투), spring(회복 샘), treasure(보물), boss(마지막 전투)
KIND_LABELS = {
    "monster": "오류 생물",
    "spring": "백업 파일 (회복 샘)",
    "treasure": "패치 파일 (보물)",
    "boss": "커널 패닉 (보스)",
}

# 갈림길에서 인식할 말 → 방향. 음성 모델 어휘에 있는 단어만 쓴다
DIRECTION_PHRASES = {"left": "left", "right": "right", "forward": "forward", "straight": "forward"}


@dataclass
class Room:
    key: str
    kind: str                 # KIND_LABELS의 key
    name: str                 # 화면에 보이는 경로 (예: "/home")
    exits: dict = field(default_factory=dict)  # 방향 → 다음 방 key. 비어 있으면 마지막 방
    stage: int | None = None  # 몬스터 방이면 battle.engine.STAGES 번호


ROOMS = {room.key: room for room in [
    Room("home", "monster", "/home", {"left": "home_backup", "right": "home_patch"}, stage=1),
    Room("home_backup", "spring", "/home/backup", {"forward": "tmp"}),
    Room("home_patch", "treasure", "/home/update.patch", {"forward": "tmp"}),

    Room("tmp", "monster", "/tmp", {"left": "tmp_patch", "right": "tmp_backup"}, stage=2),
    Room("tmp_patch", "treasure", "/tmp/hotfix.patch", {"forward": "varlog"}),
    Room("tmp_backup", "spring", "/tmp/backup", {"forward": "varlog"}),

    # 3스테이지 뒤에는 회복 샘에 들르거나, 바로 보스에게 갈 수 있다
    Room("varlog", "monster", "/var/log", {"left": "varlog_backup", "forward": "root"}, stage=3),
    Room("varlog_backup", "spring", "/var/log/backup", {"forward": "root"}),

    Room("root", "boss", "/root", stage=4),
]}

START = "home"


def get_room(key):
    """방 key → Room"""
    return ROOMS[key]


def exits(key):
    """그 방에서 갈 수 있는 [(방향, 다음 Room)]"""
    return [(direction, ROOMS[target]) for direction, target in ROOMS[key].exits.items()]


def move(key, direction):
    """방향으로 옮긴 방 key. 그 방향으로 길이 없으면 None"""
    return ROOMS[key].exits.get(direction)


def check_map():
    """모든 길에서 몬스터 방이 1, 2, 3, 4스테이지 순서로 나오고 보스 방에서 끝나는지 확인한다. 길 목록을 돌려준다."""
    paths = []

    def walk(key, path):
        path = path + [key]
        if not ROOMS[key].exits:
            paths.append(path)
        for target in ROOMS[key].exits.values():
            walk(target, path)

    walk(START, [])
    for path in paths:
        stages = [ROOMS[k].stage for k in path if ROOMS[k].kind in ("monster", "boss")]
        assert stages == [1, 2, 3, 4], f"몬스터 순서가 맞지 않는 길: {path}"
        assert ROOMS[path[-1]].kind == "boss", f"보스 방에서 끝나지 않는 길: {path}"
    for room in ROOMS.values():
        assert room.kind in KIND_LABELS, f"알 수 없는 방 종류: {room.key}"
        assert set(room.exits) <= set(DIRECTION_PHRASES.values()), f"알 수 없는 방향: {room.key}"
    return paths


if __name__ == "__main__":
    # 단독 실행: python -m world.dungeon  (지도 확인, 모든 길 출력)
    for room in ROOMS.values():
        way = ", ".join(f"{d} → {ROOMS[t].name}" for d, t in room.exits.items()) or "끝"
        print(f"{room.name:20} {KIND_LABELS[room.kind]:16} {way}")
    paths = check_map()
    print(f"\n길 {len(paths)}가지, 모두 4스테이지 순서대로 보스 방에서 끝남")
    for path in paths:
        print("  " + " > ".join(ROOMS[k].name for k in path))
