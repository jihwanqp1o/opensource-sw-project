# opensource-sw-project
오픈소스SW 팀 프로젝트 - 오픈소스를 활용한 응용 프로그램 개발

## 📌 과제 개요
- **주제**: 오픈소스 SW를 활용한 응용 프로그램 개발
- 일상에서 해결하고 싶은 문제나 만들고 싶은 서비스를 정한 뒤, 오픈 SW를 활용하여 하나의 프로그램 제작
- **프로젝트 주제**: 마법 음성 전투 게임

## 🧙 프로젝트 소개
플레이어가 마이크에 주문(파이어볼, 실드 등)을 말하면 음성을 텍스트로 인식하고, 그 주문으로 몬스터와 턴제로 싸우는 **터미널 게임**입니다.

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
```bash
python main.py              # 마이크로 주문 외치기
python main.py --keyboard   # 마이크·모델 없이 키보드로 주문 입력 (테스트용)
```
정상이면 슬라임 아스키 아트와 체력바가 나오고, 아래에 `주문을 외치세요: fireball / shield / heal`이 보입니다.
주문을 말하면(또는 입력하면) 큰 글씨 주문 이름 → 몬스터 체력 감소 → 몬스터 반격 순서로 진행되고, 끝나면 `VICTORY` 또는 `GAME OVER`가 나옵니다.

| 주문 | 말하는 법 | 효과 |
|---|---|---|
| fireball | "fireball" / "fire ball" / "fire" | 몬스터에게 20 데미지 |
| shield | "shield" | 몬스터의 다음 공격을 막음 |
| heal | "heal" | 체력 15 회복 |

### 내 모듈만 확인하기
| 명령 | 정상이면 보이는 것 |
|---|---|
| `python -m battle.engine` | 턴별 전투 기록, 마지막에 `승자: player` |
| `python -m ascii_art.monster` | 슬라임 아스키 아트 |
| `python -m ascii_art.spell_text` | 큰 글씨 `FIREBALL` |
| `python -m ui.screen` | 가짜 값으로 그린 전투 화면 |
| `python -m voice.recognizer` | "fireball"이라고 말하면 `인식 결과: fireball` |

## 📁 폴더 구조
> 폴더·파일 구조 구축과 변경은 지환([@jihwanqp1o](https://github.com/jihwanqp1o))이 담당합니다. 구조를 바꿔야 할 때는 먼저 이야기해 주세요.
> 모듈끼리 주고받는 함수 모양(연결 규칙)은 [docs/INTERFACES.md](docs/INTERFACES.md)에 있습니다.

```
opensource-sw-project/
├── main.py                  # 게임 시작점, 모듈 연결 (지환)
├── config.py                # 경로·설정값, 환경 변수로 변경 가능 (지환)
├── voice/
│   └── recognizer.py        # 마이크 → Vosk → 주문 key, 키보드 입력 (지환)
├── battle/
│   ├── spells.py            # 주문 목록 (석현)
│   └── engine.py            # 체력, 데미지, 턴 진행, 승부 판정 (석현)
├── ascii_art/
│   ├── monster.py           # 몬스터 이미지 → 아스키 아트 (태웅)
│   └── spell_text.py        # 주문 이름 큰 글씨 (태웅)
├── ui/
│   └── screen.py            # rich 화면: 체력바, 화면 분할, 피격 색 (수빈)
├── assets/monsters/         # 몬스터 이미지 (slime.png는 임시 그림)
├── models/                  # Vosk 모델 (저장소에 올리지 않음)
├── docs/INTERFACES.md       # 연결 규칙
├── .github/copilot-instructions.md  # VS Code Copilot이 자동으로 읽는 작업 규칙
├── requirements.txt         # 의존성 목록
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

### PR 절차
1. 작업 브랜치를 push하고 PR을 올립니다.
2. PR 설명에 **무엇을 바꿨는지**, **어떻게 확인했는지**를 적습니다.
3. 팀원 1명 이상 리뷰 후 지환([@jihwanqp1o](https://github.com/jihwanqp1o))이 merge합니다.
4. merge 후 로컬에서 `main`을 pull 받고, 작업 브랜치는 삭제합니다.

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

### 올리면 안 되는 것 (`.gitignore` 대상)
- Vosk 모델 파일 (`models/`)
- 가상환경 폴더 (`venv/`)
- API 키나 개인 설정 파일 (`.env`)

## ✅ 결정 사항
| 항목 | 결정 | 비고 |
|---|---|---|
| 마이크 입력 라이브러리 | sounddevice | Vosk 공식 예제와 같음 |
| 음성 인식 언어 | 영어 | 인식 단어를 주문 목록으로 제한해 정확도 확보 |
| 전투 로직 범위 | 최소 (1차) | 체력, 주문별 고정 데미지, 몬스터 1마리 고정 반격. 이후 확장은 석현 담당 |

## 🎯 평가지표 (총 100점)
| 항목 | 배점 | 평가 기준 |
|---|:---:|---|
| 1. 프로젝트 기획 및 완성도 | 25 | 프로젝트 목적이 명확하고 계획한 주요 기능이 구현되었는가<br>여러 기능이 정상적으로 연결되어 동작하며 코드가 적절하게 구성되어 있는가 |
| 2. 오픈 소스 활용 | 25 | 적절한 오픈소스 라이브러리, 패키지, API를 탐색하고 프로젝트에 적절하게 활용했는가 |
| 3. Git/GitHub 활용 및 협업 | 25 | GitHub를 이용해 버전관리 및 팀원 간 협업을 수행했는가 |
| 4. 발표 및 시연 | 25 | 개발 과정과 결과를 명확하게 설명하고 실제 프로그램을 안정적으로 시연했는가 |
