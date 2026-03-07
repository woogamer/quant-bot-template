# quant-bot-template

퀀트 스터디용 자동매매 봇 템플릿입니다.
KIS(한국투자증권) **모의투자** API를 사용하여 실제 주문 경험을 제공합니다.

## 10분 만에 내 PC에서 봇 실행하기

### 1단계: 사전 준비

- [Python 3.10+](https://www.python.org/downloads/) 설치
- [한국투자증권 모의투자](https://apiportal.koreainvestment.com/) 계정 및 API 키 발급
- [Telegram Bot](https://t.me/BotFather) 생성 후 토큰 발급

### 2단계: 프로젝트 설정

```bash
# 1. 레포 클론
git clone https://github.com/YOUR_USERNAME/quant-bot-template.git
cd quant-bot-template

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 설정 파일 생성
cp config.template.yaml config.yaml
```

### 3단계: config.yaml 수정

`config.yaml`을 열고 본인의 API 키와 텔레그램 정보를 입력하세요.

```yaml
kis:
  app_key: "발급받은_앱키"
  app_secret: "발급받은_시크릿키"
  account_no: "모의투자계좌번호"

telegram:
  bot_token: "BotFather에서_발급받은_토큰"
  chat_id: 123456789
```

> **chat_id 확인 방법**: 텔레그램에서 [@userinfobot](https://t.me/userinfobot) 에게 아무 메시지나 보내면 알려줍니다.

### 4단계: 봇 실행

```bash
python main.py
```

봇이 실행되면 텔레그램으로 시작 알림이 옵니다.
종료하려면 `Ctrl+C`를 누르세요.

## 파일 구조

```
quant-bot-template/
├── main.py               # 실행 진입점 (건드리지 마세요)
├── my_strategy.py        # 여기만 수정하세요!
├── config.template.yaml  # 설정 템플릿
├── config.yaml           # 내 설정 (git에 올라가지 않음)
├── requirements.txt      # 의존성 패키지
└── core/                 # 인프라 모듈 (건드리지 마세요)
    ├── kis_api.py        # KIS API 래퍼
    ├── telegram_bot.py   # 텔레그램 알림
    └── logger.py         # 로그 기록
```

## Claude Code로 시작하기 (추천)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code)가 설치되어 있다면, 프로젝트 폴더에서 `claude`를 실행하세요.
아래 슬래시 명령으로 Claude가 단계별로 안내해줍니다.

| 명령 | 설명 |
|------|------|
| `/setup` | 처음 시작할 때. API 키 발급부터 첫 실행까지 단계별 안내 |
| `/new-strategy` | 새 매매 전략 만들기. 원하는 전략을 말하면 Claude가 코드로 구현 |
| `/check` | 설정이 올바른지 검증 |
| `/deploy` | 서버에 봇 배포하기 (Docker) |

### 전략 바꾸기 예시

Claude Code에서 이렇게 말해보세요:

> "삼성전자가 5일 이동평균선 아래로 내려가면 매수하고, 10% 수익이 나면 매도하는 전략으로 바꿔줘"

또는 `/new-strategy`를 실행하면 Claude가 대화형으로 전략을 만들어줍니다.

## 서버에서 24시간 돌리기

Docker만 있으면 서버에서 봇을 자동으로 돌릴 수 있습니다.

```bash
# 봇 실행 (백그라운드)
docker compose up -d --build

# 로그 확인
docker compose logs -f

# 전략 수정 후 재시작
docker compose restart bot

# 봇 중지
docker compose down
```

`my_strategy.py`와 `config.yaml`은 볼륨으로 마운트되어 있어서, 파일 수정 후 `docker compose restart bot`만 하면 됩니다.

자세한 안내는 Claude Code에서 `/deploy`를 실행하세요.

## 주의사항

- 이 봇은 **모의투자** 환경에서 동작합니다. 실투자 전환 시 API URL과 tr_id를 변경해야 합니다.
- `config.yaml`에는 API 키가 들어있으므로 **절대 GitHub에 올리지 마세요**. (`.gitignore`에 포함됨)
- 장 운영시간(09:00~15:30) 외에는 전략이 실행되지 않습니다.
