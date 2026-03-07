# quant-bot-template

KIS(한국투자증권) 모의투자 자동매매 봇 템플릿. 퀀트 스터디용.

## 프로젝트 구조

```
my_strategy.py        # 사용자가 수정하는 유일한 파일
config.yaml           # API 키, 텔레그램 설정 (git 추적 안 됨)
config.template.yaml  # 설정 템플릿
main.py               # 봇 실행 진입점 (수정 금지)
core/                 # 인프라 모듈 (수정 금지)
  kis_api.py          # KIS API 래퍼 (토큰 자동 발급/갱신)
  telegram_bot.py     # 텔레그램 알림
  logger.py           # 로깅
```

## 핵심 규칙

- **수정 가능한 파일은 `my_strategy.py` 단 하나**. `core/`, `main.py`는 절대 수정하지 마세요.
- **config.yaml 내용을 터미널에 출력하거나 코드에 하드코딩하지 마세요.** API 키가 포함되어 있습니다.
- 코드는 반드시 **동기(synchronous)** 방식으로 작성하세요. async/await 사용 금지.
- 한국어 주석과 한국어 키(`현재가`, `보유종목` 등)를 사용합니다.

## 전략 작성법

`my_strategy.py`의 `generate_signal()` 함수를 수정합니다.

### 입력

```python
def generate_signal(market_data: dict, account_data: dict) -> list[dict]:
```

- `market_data`: 관심 종목의 현재가
  ```python
  {
      "005930": {"현재가": 71000, "전일대비": -500, "등락률": -0.70},
      "000660": {"현재가": 123000, "전일대비": 1000, "등락률": 0.82},
  }
  ```

- `account_data`: 계좌 잔고
  ```python
  {
      "보유종목": [
          {"종목코드": "005930", "종목명": "삼성전자", "수량": 10, "평균단가": 70000},
      ],
      "예수금": 1000000,
  }
  ```

### 출력

시그널 리스트를 반환합니다. 매매할 게 없으면 빈 리스트 `[]`.

```python
[
    {
        "ticker": "005930",   # 종목코드 (6자리 문자열)
        "action": "BUY",      # "BUY" 또는 "SELL"
        "qty": 1,             # 주문 수량 (정수)
        "price": 0,           # 지정가 (0이면 시장가)
    },
]
```

### WATCHLIST

`my_strategy.py` 하단의 `WATCHLIST`에 모니터링할 종목코드를 추가하세요.
`main.py`가 이 리스트의 종목 현재가를 조회하여 `market_data`로 전달합니다.

```python
WATCHLIST = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
]
```

## 실행

```bash
# 로컬
python main.py

# 서버 (Docker)
docker compose up -d --build
```

- 장 시간(09:00~15:30)에만 전략이 실행됩니다.
- 실행 주기는 `config.yaml`의 `bot.interval_minutes`로 설정합니다 (기본 10분).
- 종료: `Ctrl+C`

## 커스텀 스킬

스터디원은 아래 슬래시 명령으로 Claude의 도움을 받을 수 있습니다:

- `/setup` — 처음 시작할 때. 환경 설정을 단계별로 안내합니다.
- `/new-strategy` — 새로운 매매 전략을 만들거나 기존 전략을 수정합니다.
- `/check` — config.yaml과 환경이 제대로 설정되었는지 검증합니다.
- `/deploy` — 서버에 Docker로 봇을 배포합니다.
