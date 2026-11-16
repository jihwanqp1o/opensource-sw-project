# opensource-sw-project
오픈소스SW 팀 프로젝트 - 오픈소스를 활용한 응용 프로그램 개발

## ▶ 바로 플레이하기 (Windows)
Python 설치 없이 실행할 수 있어요.

| 파일 | 실행 방법 | |
|---|---|---|
| [**VoiceShell.zip 받기**](https://github.com/jihwanqp1o/opensource-sw-project/releases/latest/download/VoiceShell.zip) | 압축 풀기 → `VoiceShell.bat` 더블클릭 | 추천. 어느 Windows PC에서나 실행 |
| [VoiceShell.exe 받기](https://github.com/jihwanqp1o/opensource-sw-project/releases/latest/download/VoiceShell.exe) | 받아서 바로 더블클릭 | 빠른 실행용. 스마트 앱 컨트롤이 켜진 PC에서는 막힐 수 있음 |

- "Windows의 PC 보호" 경고가 뜨면 "추가 정보" → "실행"을 누르세요.
- exe가 "애플리케이션 제어 정책"으로 막히면 zip을 쓰세요. zip은 python.org의 서명된 공식 Python으로 실행해서 막히지 않아요.
- 모든 버전은 [Releases](https://github.com/jihwanqp1o/opensource-sw-project/releases)에 있어요.

## 📌 과제 개요
- **주제**: 오픈소스 SW를 활용한 응용 프로그램 개발
- 일상에서 해결하고 싶은 문제나 만들고 싶은 서비스를 정한 뒤, 오픈 SW를 활용하여 하나의 프로그램 제작
- **프로젝트 주제**: 마법 음성 전투 게임

## 🧙 프로젝트 소개
플레이어가 마이크에 주문(파이어볼, 실드 등)을 말하면 음성을 텍스트로 인식하고, 그 주문으로 몬스터와 턴제로 싸우는 **터미널 게임**입니다.

> **콘셉트: 터미널 속 마법사** — 키보드가 고장 난 낡은 터미널 안에서, 목소리로 명령(주문)을 외쳐 오류 몬스터를 물리치고 시스템을 복구합니다. 자세한 세계관과 이름 규칙은 [docs/CONCEPT.md](docs/CONCEPT.md)에 있어요.

### 게임 흐름
1. 화면에 몬스터(아스키 아트)와 양쪽 체력 게이지가 표시됩니다.
2. 플레이어가 마이크에 주문을 외칩니다. (영창)
3. 인식된 주문 이름이 큰 아스키 글씨로 출력되고 주문이 발동합니다.
4. 몬스터 피격 연출이 나오고 체력이 줄어듭니다.
5. 몬스터가 반격합니다.
6. 어느 한쪽의 체력이 0이 될 때까지 2~5를 반복합니다.

### 주요 기능
| 기능 | 설명 | 사용 오픈소스 |
|---|---|---|
| 음성 주문 인식 | 마이크 입력 → 실시간 텍스트 변환 → 주문 발동 | [Vosk](https://alphacephei.com/vosk/) (로컬 모델) |
| 몬스터 아스키 변환 | 몬스터 이미지를 명도 기준으로 문자로 바꿔 출력 | [Pillow](https://python-pillow.org/) |
| 주문 이름 강조 | 외친 주문 이름을 큰 아스키 글씨로 출력 | [pyfiglet](https://github.com/pwaller/pyfiglet) |
| 턴제 전투와 화면 UI | 영창 → 피격 연출 → 몬스터 반격, 체력 게이지, 화면 분할 | [rich](https://github.com/Textualize/rich) |

### 기술 스택
- Python
- Vosk, Pillow, pyfiglet, rich
- 마이크 입력: sounddevice
- 음성 인식 언어: 영어 (주문을 영어로 외침)

## ⚙️ 설치와 실행
Python 3.12(64비트)에서 확인했습니다.

### 1. 저장소 받기
```bash
git clone https://github.com/jihwanqp1o/opensource-sw-project.git
cd opensource-sw-project
```

### 2. 가상환경 만들기
```bash
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate
```

### 3. 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 4. Vosk 모델 내려받기
1. [vosk-model-small-en-us-0.15.zip](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip)(약 40MB)을 내려받습니다.
2. 압축을 풀어 프로젝트 루트의 `models/` 폴더 아래에 둡니다.
   ```
   opensource-sw-project/
   └── models/
       └── vosk-model-small-en-us-0.15/   ← 압축 푼 폴더 (안에 am, conf, graph 폴더가 있어야 함)
   ```
3. 모델 파일은 용량이 크므로 **저장소에 올리지 않습니다.** (`.gitignore`에 들어 있음)
4. 다른 위치에 두었다면 환경 변수 `VOSK_MODEL_PATH`로 경로를 알려 줍니다.
   ```powershell
   $env:VOSK_MODEL_PATH = "D:\vosk\vosk-model-small-en-us-0.15"   # PowerShell
   ```

### 5. 실행
실행 방법은 두 가지이고, 화면이 다릅니다.

| 모드 | 명령 | 용도 | 화면 |
|---|---|---|---|
| 플레이 모드 | `python main.py` | 시연, 실제 플레이 (마이크) | 타이틀 → 전투 → 결과 화면 |
| 테스트 모드 | `python main.py --test` | 개발 중 확인 (키보드) | 메뉴 없이 바로 전투, 맨 위에 노란 `TEST MODE` 줄 |

`--keyboard`는 `--test`와 같은 뜻입니다. 마이크 없이 플레이 모드 흐름을 보고 싶으면 `$env:INPUT_MODE = "keyboard"`를 먼저 실행하세요.

**플레이 모드**: 타이틀 화면에서 `Enter` 시작, `H` 주문 목록, `Q` 종료. 주문을 말하면 큰 글씨 주문 이름 → 몬스터 체력 감소 → 몬스터 반격 순서로 진행되고, 끝나면 `SYSTEM RESTORED`(승리) 또는 `SEGMENTATION FAULT`(패배)와 함께 걸린 시간, 사용한 주문, 명령 인식 횟수가 나옵니다.

**테스트 모드**: 바로 전투가 시작되고 `주문 입력>`에 주문 이름을 칩니다. 끝나면 `VICTORY` 또는 `GAME OVER`를 출력하고 종료합니다.

| 주문 | 말하는 법 | 효과 |
|---|---|---|
| fireball | "fireball" / "fire ball" / "fire" | 몬스터에게 25 데미지 |
| lightning | "lightning" / "thunder" | 몬스터에게 15 데미지, 40% 확률로 크리티컬 50 데미지 |
| shield | "shield" / "protect" / "defend" | 몬스터의 다음 공격을 완전히 막음 |
| heal | "heal" / "cure" / "health" | 체력 20 회복 (최대 100) |

- 플레이어 체력 100, 몬스터(슬라임) 체력 80
- 몬스터는 기본 공격(15)과 강화 공격(20)을 번갈아 씁니다.
- 주문을 알아듣지 못하면 플레이어 턴이 넘어가고 몬스터가 공격합니다.

### 내 모듈만 확인하기
| 명령 | 정상이면 보이는 것 |
|---|---|
| `python -m battle.engine` | 턴별 전투 기록, 마지막에 `승자: player` |
| `python -m ascii_art.monster` | 슬라임 아스키 아트 |
| `python -m ascii_art.spell_text` | 큰 글씨 `FIREBALL` |
| `python -m ui.screen` | 가짜 값으로 그린 전투 화면 |
| `python -m ui.menu` | 타이틀, 주문 목록, 결과 화면, TEST MODE 줄 |
| `python -m voice.recognizer` | "fireball"이라고 말하면 `인식 결과: fireball` |
| `python -m voice.recognizer --devices` | 마이크 번호 목록 (`*`가 기본 마이크) |
| `python -m voice.experiment --speaker 이름` | 안내에 따라 말하면 마지막에 정답률 요약표 ([실험 문서](docs/experiments/voice-accuracy.md)) |

### 실행 환경과 마이크 설정
- 게임 화면이 40줄 정도 되니 **PowerShell 창을 최대화한 상태**에서 실행해 주세요.
- 마이크 모드에서는 화면 맨 아래에 남은 시간과 들린 말이 표시됩니다. 주문을 말하고 잠깐 멈추면 인식되고, 10초 안에 주문이 인식되지 않으면 턴이 넘어갑니다. 시간은 환경 변수 `VOICE_TIMEOUT`(초)로 바꿀 수 있습니다.
- 마이크가 여러 개라 원하지 않는 마이크로 잡히면, 번호를 확인해서 지정합니다.
  ```powershell
  python -m voice.recognizer --devices   # 마이크 번호 확인 (*가 기본 마이크)
  $env:MIC_DEVICE = "9"                  # 사용할 번호 지정 (이 창에서만 유지)
  python main.py
  ```

## 📁 폴더 구조
> 폴더·파일 구조 구축과 변경은 지환([@jihwanqp1o](https://github.com/jihwanqp1o))이 담당합니다. 구조를 바꿔야 할 때는 먼저 이야기해 주세요.
> 모듈끼리 주고받는 함수 모양(연결 규칙)은 [docs/INTERFACES.md](docs/INTERFACES.md)에 있습니다.

```
opensource-sw-project/
├── main.py                  # 게임 시작점, 모듈 연결 (지환)
├── config.py                # 경로·설정값, 환경 변수로 변경 가능 (지환)
├── voice/
│   ├── recognizer.py        # 마이크 → Vosk → 주문 key, 키보드 입력 (지환)
│   └── experiment.py        # 음성 인식 정확도 실험 (지환)
├── battle/
│   ├── spells.py            # 주문 목록 (석현)
│   └── engine.py            # 체력, 데미지, 턴 진행, 승부 판정 (석현)
├── ascii_art/
│   ├── monster.py           # 몬스터 이미지 → 아스키 아트 (태웅)
│   └── spell_text.py        # 주문 이름 큰 글씨 (태웅)
├── ui/
│   ├── screen.py            # rich 전투 화면: 체력바, 화면 분할, 피격 색 (수빈)
│   └── menu.py              # 타이틀, 주문 목록, 결과 화면, TEST MODE 줄 (수빈)
├── assets/monsters/         # 몬스터 이미지 (slime.png는 임시 그림)
├── models/                  # Vosk 모델 (저장소에 올리지 않음)
├── docs/
│   ├── INTERFACES.md        # 연결 규칙
│   └── experiments/         # 음성 인식 정확도 실험 결과
├── .github/copilot-instructions.md  # VS Code Copilot이 자동으로 읽는 작업 규칙
├── packaging/               # 배포 파일(zip, exe) 만들기: build.py, READ_ME.txt (지환)
├── requirements.txt         # 의존성 목록
├── requirements-dev.txt     # 배포 파일 빌드용 (PyInstaller)
├── CLAUDE.md                # Claude Code용 작업 규칙
└── README.md
```

## 🤖 Copilot으로 작업할 때
- VS Code Copilot Chat은 `.github/copilot-instructions.md`를 자동으로 읽습니다. 따로 붙여 넣을 필요가 없습니다.
- 질문할 때는 **내 담당 파일**을 열어 둔 상태에서 "이 파일의 ○○ 함수에서 ○○를 바꿔 줘"처럼 범위를 좁혀 요청하세요.
- Copilot이 내 담당 폴더 밖 파일이나 함수 이름·인자를 바꾸려 하면 받아들이지 말고 담당자와 상의하세요.
- 고친 뒤에는 위의 "내 모듈만 확인하기" 명령과 `python main.py --keyboard`로 확인한 뒤 PR을 올립니다.

## 👥 팀원과 역할 분담
| 이름 | GitHub | 역할 |
|---|---|---|
| 수빈 | [@ysb2477](https://github.com/ysb2477) | 프론트엔드 (UI, UX, 디자인) |
| 지환 | [@jihwanqp1o](https://github.com/jihwanqp1o) | 백엔드 - 음성 변환 시스템<br>저장소 관리 (main merge, 프로젝트 구조 구축) |
| 석현 | [@Hongsee16](https://github.com/Hongsee16) | 백엔드 - 전투 로직 및 턴 진행 |
| 태웅 | [@edon1222](https://github.com/edon1222) | 백엔드 - 이미지 아스키 변환 |
| 제형 | [@miuomshelter](https://github.com/miuomshelter) | 발표 |
| 태양 | [@rupee-1025](https://github.com/rupee-1025) | QA(게임 플레이) 및 자료 정리 |

## 🤝 협업 방법
### 브랜치
- `main`에 직접 push하지 않습니다.
- 기능별 브랜치를 만들어 작업합니다. 예: `feature/voice-input`

### 커밋 메시지
| 접두사 | 용도 |
|---|---|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 |
| `refactor` | 구조 변경 |

예: `fix: 주문 이름 대소문자 인식 오류 수정`

### 이슈
- 할 일과 버그는 [Issues](https://github.com/jihwanqp1o/opensource-sw-project/issues)에 등록합니다. 담당자(Assignees)와 모듈 라벨(`voice`, `battle`, `ui`, `ascii-art`, `main`, `qa`, `presentation`)을 붙입니다.
- 작업은 내게 배정된 이슈에서 시작하고, PR에 `Closes #이슈번호`를 적으면 merge될 때 이슈가 자동으로 닫힙니다.

### PR 절차
1. 작업 브랜치를 push하고 PR을 올립니다.
2. PR을 열면 템플릿이 자동으로 나옵니다. **무엇을 바꿨는지**, **어떻게 확인했는지**, **관련 이슈**를 채우고 체크리스트를 확인합니다.
3. 팀원 1명 이상 리뷰(Approve) 후 지환([@jihwanqp1o](https://github.com/jihwanqp1o))이 merge합니다. main은 승인 없이는 merge되지 않도록 보호되어 있습니다.
4. merge 후 로컬에서 `main`을 pull 받고, 작업 브랜치는 삭제합니다.

### 리뷰하는 법
Approve만 누르지 말고 **코멘트를 한두 줄이라도** 남겨 주세요. 리뷰 기록이 협업 평가 자료가 됩니다.
1. PR의 **Files changed** 탭에서 바뀐 내용을 봅니다. 궁금하거나 고칠 점이 있는 줄은 줄 번호 옆 `+`를 눌러 코멘트를 남깁니다.
2. 직접 실행해 봅니다.
   ```bash
   git fetch origin
   git checkout 브랜치이름        # PR 상단에 적힌 브랜치
   python main.py --keyboard
   git checkout main              # 확인 후 돌아오기
   ```
3. 아래를 확인합니다.
   - PR 설명대로 동작하는가
   - 담당 폴더 밖 파일이나 함수 모양(연결 규칙)이 바뀌지 않았는가
   - 게임 전체(`python main.py --keyboard`)가 여전히 끝까지 진행되는가
4. **Review changes** 버튼에서 결과를 고릅니다.
   - Approve: 문제 없음 (좋았던 점 한 줄이라도 적기)
   - Comment: 의견만 남김
   - Request changes: 고쳐야 merge 가능

Copilot에게 리뷰를 도와 달라고 할 때는 이렇게 요청하면 됩니다.
```
PR 브랜치 "브랜치이름"과 main의 차이를 보여 주고, 연결 규칙(docs/INTERFACES.md)을 어긴 부분이나 버그가 있는지 확인해 줘. 그리고 python main.py --keyboard로 실행해 줘.
```

```bash
git checkout -b feature/voice-input
# 작업 후
git add .
git commit -m "feat: 마이크 입력 연결"
git push -u origin feature/voice-input
# GitHub에서 PR 생성 → 리뷰 → merge
git checkout main
git pull
git branch -d feature/voice-input
```

### 자동 확인 (CI)
PR을 올리면 GitHub Actions(CI)가 Windows와 Ubuntu에서 모듈 단독 실행과 `python main.py --keyboard`를 자동으로 돌립니다. PR 화면 아래에 초록 체크가 뜨면 통과, 빨간 X면 **Details**를 눌러 어느 단계에서 실패했는지 확인하세요.

### 배포 파일 만들기 (지환)
`v0.1.0`처럼 버전 태그를 올리면 GitHub Actions가 휴대용 zip과 exe를 만들어 [Releases](https://github.com/jihwanqp1o/opensource-sw-project/releases)에 올립니다. 내 PC에서 직접 만들려면 아래처럼 하면 되고, 결과는 `dist/release/`에 생깁니다.
```powershell
pip install -r requirements-dev.txt
python packaging/build.py
```

### 올리면 안 되는 것 (`.gitignore` 대상)
- Vosk 모델 파일 (`models/`)
- 가상환경 폴더 (`venv/`)
- API 키나 개인 설정 파일 (`.env`)

## ✅ 결정 사항
| 항목 | 결정 | 비고 |
|---|---|---|
| 마이크 입력 라이브러리 | sounddevice | Vosk 공식 예제와 같음 |
| 음성 인식 언어 | 영어 | 인식 단어를 주문 목록으로 제한해 정확도 확보 |
| 전투 로직 범위 | 주문 4종 + 몬스터 공격 패턴 | 번개 확률 크리티컬, 몬스터 기본/강화 공격 교대, 인식 실패 시 턴 넘김. 몬스터 추가 등 이후 확장은 미정 (석현 담당) |

## 📄 라이선스
이 프로젝트는 [MIT License](LICENSE)를 따릅니다.

### 사용한 오픈소스
| 이름 | 용도 | 라이선스 |
|---|---|---|
| [Vosk](https://github.com/alphacep/vosk-api) | 음성 인식 | Apache-2.0 |
| [vosk-model-small-en-us-0.15](https://alphacephei.com/vosk/models) | 영어 음성 인식 모델 (저장소에 포함하지 않음) | Apache-2.0 |
| [sounddevice](https://github.com/spatialaudio/python-sounddevice) | 마이크 입력 | MIT |
| [Pillow](https://github.com/python-pillow/Pillow) | 몬스터 이미지 처리 | MIT-CMU |
| [pyfiglet](https://github.com/pwaller/pyfiglet) | 주문 이름 큰 글씨 | MIT |
| [rich](https://github.com/Textualize/rich) | 터미널 화면 UI | MIT |

모두 상업적 이용과 수정이 허용되는 라이선스이며 MIT 라이선스인 이 프로젝트와 함께 쓸 수 있습니다. Apache-2.0인 Vosk는 재배포할 때 원본 라이선스 고지를 유지해야 합니다.

### 이미지·리소스 출처
| 파일 | 출처 | 라이선스 |
|---|---|---|
| `assets/monsters/slime.png` | 팀 자체 제작 (Pillow로 그린 임시 그림) | MIT (이 프로젝트) |

새 이미지나 리소스를 추가할 때는 직접 만들었거나 사용이 허용된 라이선스(CC0 등)인지 확인하고, 이 표에 출처를 함께 적습니다.

## 🎯 평가지표 (총 100점)
| 항목 | 배점 | 평가 기준 |
|---|:---:|---|
| 1. 프로젝트 기획 및 완성도 | 25 | 프로젝트 목적이 명확하고 계획한 주요 기능이 구현되었는가<br>여러 기능이 정상적으로 연결되어 동작하며 코드가 적절하게 구성되어 있는가 |
| 2. 오픈 소스 활용 | 25 | 적절한 오픈소스 라이브러리, 패키지, API를 탐색하고 프로젝트에 적절하게 활용했는가 |
| 3. Git/GitHub 활용 및 협업 | 25 | GitHub를 이용해 버전관리 및 팀원 간 협업을 수행했는가 |
| 4. 발표 및 시연 | 25 | 개발 과정과 결과를 명확하게 설명하고 실제 프로그램을 안정적으로 시연했는가 |
