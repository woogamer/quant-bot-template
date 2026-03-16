# quant-bot-template

> KIS(한국투자증권) **모의투자** 자동매매 봇 템플릿 — 퀀트 스터디용

파일 하나(`my_strategy.py`)만 수정하면 나만의 자동매매 봇이 완성됩니다.
API 연동, 주문 실행, 텔레그램 알림은 모두 구현되어 있습니다.

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

## 빠른 시작 (5분)

### 1. 사전 준비

| 항목 | 링크 |
|------|------|
| Python 3.10+ | [다운로드](https://www.python.org/downloads/) |
| KIS 모의투자 API 키 | [API포탈](https://apiportal.koreainvestment.com/) 에서 모의투자 신청 → 앱키 발급 |
| Telegram Bot 토큰 | [@BotFather](https://t.me/BotFather) 에서 봇 생성 |

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
  account_no: "12345678-01"    # 모의투자 계좌번호

telegram:
  bot_token: "BotFather에서_발급받은_토큰"
  chat_id: 123456789
```

> **chat_id 확인**: [@userinfobot](https://t.me/userinfobot) 에게 아무 메시지나 보내면 알려줍니다.

### 4. 실행

```bash
python main.py
```

텔레그램으로 시작 알림이 오면 성공! 종료는 `Ctrl+C`.

---

## 전략 작성법

`my_strategy.py`의 `generate_signal()` 함수를 수정합니다. 이 함수가 매매의 핵심입니다.

### 입력 데이터

```python
def generate_signal(market_data: dict, account_data: dict) -> list[dict]:
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

### 출력 형식

시그널 리스트를 반환합니다. 매매할 게 없으면 빈 리스트 `[]`.

```python
return [
    {
        "ticker": "005930",   # 종목코드 (6자리 문자열)
        "action": "BUY",      # "BUY" 또는 "SELL"
        "qty": 1,             # 주문 수량 (정수)
        "price": 0,           # 지정가 (0이면 시장가)
    },
]
```

### WATCHLIST

파일 하단의 `WATCHLIST`에 모니터링할 종목을 등록하세요. 여기 등록된 종목만 `market_data`로 들어옵니다.

```python
WATCHLIST = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
]
```

### 전략 예시

**예시 1: 단순 지정가 매수**
```python
# 삼성전자가 7만원 이하면 1주 시장가 매수
samsung = market_data.get("005930")
if samsung and samsung["현재가"] <= 70000:
    signals.append({"ticker": "005930", "action": "BUY", "qty": 1, "price": 0})
```

**예시 2: 등락률 기반 매수**
```python
# 전일 대비 3% 이상 하락한 종목 매수
for ticker, data in market_data.items():
    if data["등락률"] <= -3.0:
        signals.append({"ticker": ticker, "action": "BUY", "qty": 1, "price": 0})
```

**예시 3: 수익률 기반 매도**
```python
# 보유 종목이 평균단가 대비 10% 이상 수익이면 매도
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
💡 Claude Code에서 이렇게 말해보세요:

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
├── my_strategy.py        # ✏️ 이 파일만 수정하세요!
├── main.py               # 봇 실행 진입점 (수정 금지)
├── config.template.yaml  # 설정 템플릿
├── config.yaml           # 내 설정 (git에 올라가지 않음)
├── requirements.txt
├── Dockerfile
├── compose.yaml
└── core/                 # 인프라 모듈 (수정 금지)
    ├── kis_api.py        # KIS API 래퍼 (토큰 자동 발급/갱신)
    ├── telegram_bot.py   # 텔레그램 알림
    └── logger.py         # 로깅
```

## 동작 방식

```
main.py 실행
  → config.yaml 읽기
  → KIS 인증 (자동)
  → 10분마다 반복:
      1. WATCHLIST 종목의 현재가 조회 → market_data
      2. 계좌 잔고 조회 → account_data
      3. generate_signal(market_data, account_data) 호출
      4. 반환된 시그널대로 매수/매도 주문 실행
      5. 텔레그램으로 주문 결과 알림
```

- 장 시간(09:00~15:30)에만 전략이 실행됩니다.
- 실행 주기는 `config.yaml`의 `bot.interval_minutes`로 설정합니다 (기본 10분).

## 주의사항

- 이 봇은 **모의투자** 환경에서 동작합니다. 실투자 전환 시 API URL과 tr_id를 변경해야 합니다.
- `config.yaml`에는 API 키가 포함되어 있으므로 **절대 GitHub에 올리지 마세요** (`.gitignore`에 포함됨).
- 장 운영시간(09:00~15:30) 외에는 전략이 실행되지 않습니다.

## 라이선스

MIT
