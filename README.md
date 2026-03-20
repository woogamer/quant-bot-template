# quant-bot-template

> KIS(한국투자증권) **모의투자** 자동매매 봇 템플릿 — 퀀트 스터디용

파일 하나(`my_strategy.py`)만 수정하면 나만의 자동매매 봇이 완성됩니다.
API 연동, 주문 실행, 알림(Telegram + Slack)은 모두 구현되어 있습니다.

```
┌─────────────────────────────────────────────────┐
│  내가 수정하는 파일은 my_strategy.py 단 하나!   │
│                                                 │
│  시세 조회 → generate_signal() → 주문 실행      │
│              ^^^^^^^^^^^^^^^^                   │
│              여기에 매매 로직 작성               │
└─────────────────────────────────────────────────┘
```

---

## 기본 탑재 전략

현재 `my_strategy.py`에는 **데이트레이딩 전략**이 구현되어 있습니다.

### 진입 (매수)

MA10(10일 이동평균) 기울기로 종목별 장세를 판단합니다.

| 장세 | 판단 기준 | 매수 조건 |
|------|-----------|-----------|
| 상승추세 | MA10이 5일 전보다 +2% 이상 상승 | 현재가 < MA10 (눌림목 매수) |
| 횡보 | MA10 변동 +/-2% 이내 | 현재가가 10일 저가 근처 (밴드 하단 매수) |
| 하락추세 | MA10이 5일 전보다 -2% 이상 하락 | 매수 안 함 |

- 거래량 필터: 당일 거래량이 10일 평균의 70% 이상일 때만 진입 (장중 시간 보정 적용)
- 비중 관리: 종목당 총자산의 최대 20%

### 청산 (매도)

- 익절: 수익률 +2% 이상
- 손절: 수익률 -1.5% 이하
- 장마감: 15:00 이후 보유종목 전량 청산

### 알림

매수/매도 시 Telegram과 Slack으로 실시간 알림이 갑니다.

```
📈 [BUY] 삼성전자(005930) / 10주
   상승추세 눌림목 (현재가 195,000 < MA10 200,350)

📉 [SELL] SK하이닉스(000660) / 5주
   수익률 +2.15% / +10,750원
   익절
```

장 마감 시 일일 리포트가 전송됩니다.

```
📊 일일 리포트 (2026-03-20)

🌍 KOSPI: 5,799.38 (+0.63%)

💰 매매 내역 (매수 2건 / 매도 3건)
  📈 09:15 BUY 삼성전자 10주 [상승추세 눌림목]
  📉 11:30 SELL 삼성전자 10주 (+2.15% / +4,300원) [익절]
  ...

🎯 실현 손익: +12,500원

💼 보유 현황
  LG화학 1주 (+0.33%)
  예수금: 10,000,000원
```

### 설정값 커스터마이징

`my_strategy.py` 상단의 설정값을 바꾸면 전략 파라미터를 조절할 수 있습니다.

```python
TAKE_PROFIT = 0.02      # 익절 기준 (2%)
STOP_LOSS = -0.015      # 손절 기준 (-1.5%)
MAX_WEIGHT = 0.20       # 종목당 최대 비중 (20%)
MA_PERIOD = 10          # 이동평균 기간
VOLUME_FILTER = 0.7     # 거래량 필터 배수
CLOSE_HOUR = 15         # 장마감 청산 시각
```

### 모니터링 종목

WATCHLIST에 KOSPI 시총 상위 30종목이 등록되어 있습니다. 종목을 추가/삭제하려면 `STOCK_NAMES` 딕셔너리를 수정하세요.

---

## 빠른 시작 (5분)

### 1. 사전 준비

| 항목 | 링크 |
|------|------|
| Python 3.10+ | [다운로드](https://www.python.org/downloads/) |
| KIS 모의투자 API 키 | [API포탈](https://apiportal.koreainvestment.com/) 에서 모의투자 신청 후 앱키 발급 |
| Telegram Bot 토큰 (선택) | [@BotFather](https://t.me/BotFather) 에서 봇 생성 |
| Slack Webhook (선택) | [Slack API](https://api.slack.com/apps) 에서 Incoming Webhook 생성 |

> Telegram과 Slack 중 하나만 설정해도 됩니다. 둘 다 설정하면 동시에 알림이 갑니다.

### 2. 설치

```bash
git clone https://github.com/woogamer/quant-bot-template.git
cd quant-bot-template
pip install -r requirements.txt
cp config.template.yaml config.yaml
```

### 3. 설정

`config.yaml`을 열고 본인의 정보를 입력하세요.

```yaml
kis:
  app_key: "발급받은_앱키"
  app_secret: "발급받은_시크릿키"
  account_no: "5012345601"    # 모의투자 계좌번호 (10자리, 하이픈 없이)

telegram:
  bot_token: "BotFather에서_발급받은_토큰"
  chat_id: 123456789

slack:
  webhook_url: "https://hooks.slack.com/services/..."   # 선택

bot:
  interval_minutes: 3       # 전략 실행 주기 (분)
```

> **chat_id 확인**: [@userinfobot](https://t.me/userinfobot) 에게 아무 메시지나 보내면 알려줍니다.

> **계좌번호**: 하이픈 없이 10자리로 입력하세요 (예: `5012345601`).

### 4. 실행

```bash
python main.py
```

Telegram/Slack으로 시작 알림이 오면 성공! 종료는 `Ctrl+C`.

---

## 나만의 전략 만들기

`my_strategy.py`의 `generate_signal()` 함수를 수정합니다.

### 입력 데이터

```python
def generate_signal(market_data: dict, account_data: dict, kis=None) -> list[dict]:
```

**market_data** — 관심 종목의 현재가

```python
market_data["005930"]["현재가"]    # 71000 (int)
market_data["005930"]["전일대비"]  # -500  (int)
market_data["005930"]["등락률"]    # -0.70 (float, %)
```

**account_data** — 내 계좌 잔고

```python
account_data["예수금"]                   # 1000000 (int, 주문 가능 금액)
account_data["보유종목"][0]["종목코드"]   # "005930"
account_data["보유종목"][0]["종목명"]     # "삼성전자"
account_data["보유종목"][0]["수량"]       # 10
account_data["보유종목"][0]["평균단가"]   # 70000
```

**kis** — KIS API 클라이언트 (일별 시세 등 추가 데이터 조회용)

### 출력 형식

시그널 리스트를 반환합니다. 매매할 게 없으면 빈 리스트 `[]`.

```python
return [
    {
        "ticker": "005930",   # 종목코드 (6자리 문자열)
        "action": "BUY",      # "BUY" 또는 "SELL"
        "qty": 1,             # 주문 수량 (정수)
        "price": 0,           # 지정가 (0이면 시장가)
        "name": "삼성전자",   # 종목명 (선택 — 알림에 표시)
        "reason": "눌림목",   # 매매 사유 (선택 — 알림에 표시)
    },
]
```

### 전략 예시

**예시 1: 단순 지정가 매수**
```python
samsung = market_data.get("005930")
if samsung and samsung["현재가"] <= 70000:
    signals.append({"ticker": "005930", "action": "BUY", "qty": 1, "price": 0})
```

**예시 2: 등락률 기반 매수**
```python
for ticker, data in market_data.items():
    if data["등락률"] <= -3.0:
        signals.append({"ticker": ticker, "action": "BUY", "qty": 1, "price": 0})
```

**예시 3: 수익률 기반 매도**
```python
for h in account_data["보유종목"]:
    ticker = h["종목코드"]
    current = market_data.get(ticker, {}).get("현재가", 0)
    if current > 0 and current >= h["평균단가"] * 1.10:
        signals.append({"ticker": ticker, "action": "SELL", "qty": h["수량"], "price": 0})
```

---

## Claude Code 연동 (추천)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code)가 설치되어 있다면, 프로젝트 폴더에서 `claude`를 실행하세요.

| 명령 | 설명 |
|------|------|
| `/setup` | 처음 시작할 때. API 키 발급부터 첫 실행까지 단계별 안내 |
| `/new-strategy` | 새 매매 전략 만들기. 원하는 전략을 말하면 코드로 구현 |
| `/check` | config.yaml과 환경이 제대로 설정되었는지 검증 |
| `/deploy` | 서버에 Docker로 봇 배포하기 |

```
예시: Claude Code에서 이렇게 말해보세요:

"삼성전자가 5일 이동평균선 아래로 내려가면 매수하고,
 10% 수익이 나면 매도하는 전략으로 바꿔줘"
```

---

## 서버에서 24시간 돌리기

Docker만 있으면 됩니다.

```bash
docker compose up -d --build     # 시작
docker compose logs -f           # 로그 확인
docker compose restart bot       # 전략 수정 후 재시작
docker compose down              # 중지
```

`my_strategy.py`와 `config.yaml`은 볼륨 마운트되어 있어서, 파일 수정 후 `restart`만 하면 반영됩니다.

---

## 프로젝트 구조

```
quant-bot-template/
├── my_strategy.py        # 매매 전략 (이 파일을 수정하세요!)
├── main.py               # 봇 실행 진입점
├── config.template.yaml  # 설정 템플릿
├── config.yaml           # 내 설정 (git에 올라가지 않음)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── core/                 # 인프라 모듈
    ├── kis_api.py        # KIS API 래퍼 (토큰 자동 발급/갱신, 5xx 자동 재시도)
    ├── telegram_bot.py   # Telegram 알림
    ├── slack_bot.py      # Slack 알림
    ├── notifier.py       # 멀티 채널 알림 통합 (CompositeNotifier)
    └── logger.py         # 로깅
```

## 동작 방식

```
main.py 실행
  → config.yaml 읽기
  → KIS 인증 (자동)
  → 3분마다 반복:
      1. WATCHLIST 종목의 현재가 조회 → market_data
      2. 계좌 잔고 조회 → account_data
      3. generate_signal(market_data, account_data, kis) 호출
      4. 반환된 시그널대로 매수/매도 주문 실행
      5. Telegram + Slack으로 주문 결과 알림
      6. 15:00 이후 일일 리포트 전송 (KOSPI 지수, 매매 내역, 손익)
```

- 장 시간(09:00~15:30)에만 전략이 실행됩니다.
- 실행 주기는 `config.yaml`의 `bot.interval_minutes`로 설정합니다 (기본 3분).
- KIS 모의투자 API의 간헐적 500 에러는 자동 재시도(최대 3회)로 처리됩니다.

## 주의사항

- 이 봇은 **모의투자** 환경에서 동작합니다. 실투자 전환 시 API URL과 tr_id를 변경해야 합니다.
- `config.yaml`에는 API 키가 포함되어 있으므로 **절대 GitHub에 올리지 마세요** (`.gitignore`에 포함됨).
- 계좌번호는 **하이픈 없이 10자리**로 입력하세요 (예: `5012345601`).

## 라이선스

MIT
