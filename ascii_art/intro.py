"""게임을 켜면 나오는 부팅 오프닝. 10초 안에 콘셉트(키보드 고장, 음성 명령)가 전달되게 한다.

문구와 분위기는 docs/CONCEPT.md의 "오프닝"을 따른다. 화면에 찍는 건 main.py가 한다.
"""

OK = "[bold bright_green][ OK ][/]"
FAIL = "[bold bright_red][FAIL][/]"


def boot_lines() -> list[tuple[str, float]]:
    """(출력할 한 줄, 그 줄을 찍은 뒤 기다릴 초) 목록. 글자는 rich 색 표시를 쓸 수 있다."""
    return [
        ("[bright_green]VOICE SHELL BIOS v0.1[/]", 0.6),
        ("", 0.2),
        (f"메모리 검사 ............ {FAIL} 오류 생물 4개체 감지", 1.0),
        ("  - /home      메모리 누수 슬라임", 0.3),
        ("  - /tmp       버그 고블린", 0.3),
        ("  - /var/log   좀비 프로세스", 0.3),
        ("  - /root      [bold bright_red]커널 패닉 드래곤[/]", 0.8),
        (f"키보드 ................. {FAIL} 응답 없음", 1.0),
        (f"마이크 ................. {OK}", 0.8),
        ("", 0.2),
        ("[bold white]음성 명령 모드로 전환합니다.[/]", 0.8),
        ("[bold white]관리자님, 주문을 외쳐 시스템을 복구해 주세요.[/]", 1.8),
    ]


if __name__ == "__main__":
    # 단독 실행: python -m ascii_art.intro  (오프닝이 한 줄씩 찍힌다)
    import time

    from rich.console import Console

    console = Console()
    for line, delay in boot_lines():
        console.print(line)
        time.sleep(delay)
