# quant-bot-template

KIS(한국투자증권) 모의투자 자동매매 봇 템플릿. 퀀트 스터디용.

## 프로젝트 구조

```
my_strategy.py        # 사용자가 수정하는 유일한 파일
config.yaml           # API 키, 알림 설정 (git 추적 안 됨)
config.template.yaml  # 설정 템플릿
main.py               # 봇 실행 진입점 (수정 금지)
core/                 # 인프라 모듈 (수정 금지)
  kis_api.py          # KIS API 래퍼 (토큰 자동 발급/갱신, 5xx 자동 재시도)
  telegram_bot.py     # Telegram 알림 (HTML 모드)
  slack_bot.py        # Slack 알림 (Incoming Webhook)
  notifier.py         # 멀티 채널 알림 통합 (CompositeNotifier)
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
def generate_signal(market_data: dict, account_data: dict, kis=None) -> list[dict]:
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

- `kis`: KIS API 클라이언트 (일별 시세 등 추가 데이터 조회용). `kis.get_price()`, `kis.get_investor_trend()` 등 사용 가능. `core/kis_api.py`의 `_request_with_retry`를 import하여 커스텀 API 호출도 가능.

### 출력

시그널 리스트를 반환합니다. 매매할 게 없으면 빈 리스트 `[]`.

```python
[
    {
        "ticker": "005930",   # 종목코드 (6자리 문자열)
        "action": "BUY",      # "BUY" 또는 "SELL"
        "qty": 1,             # 주문 수량 (정수)
        "price": 0,           # 지정가 (0이면 시장가)
        "name": "삼성전자",   # 종목명 (선택 — 알림에 표시)
        "reason": "눌림목",   # 매매 사유 (선택 — 알림에 표시)
        "pnl_pct": 2.03,      # 수익률 % (선택 — 매도 시 알림에 표시)
        "pnl_amt": 6000,      # 수익금 (선택 — 매도 시 알림에 표시)
    },
]
```

### WATCHLIST / STOCK_NAMES

`my_strategy.py` 하단의 `STOCK_NAMES` 딕셔너리에 종목코드와 종목명을 등록하세요.
`WATCHLIST`는 `STOCK_NAMES.keys()`에서 자동 생성됩니다.

```python
STOCK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}
WATCHLIST = list(STOCK_NAMES.keys())
```

## 알림

- Telegram과 Slack을 동시 지원합니다 (CompositeNotifier).
- 설정된 채널에만 알림이 갑니다.
- 매수/매도 시 종목명, 사유, 수익률이 포함된 알림이 전송됩니다.
- 15:00 이후 일일 리포트가 전송됩니다 (KOSPI 지수, 매매 내역, 실현 손익, 보유 현황).

## 실행

```bash
# 로컬
python main.py

# 서버 (Docker)
docker compose up -d --build
```

- 장 시간(09:00~15:30)에만 전략이 실행됩니다.
- 실행 주기는 `config.yaml`의 `bot.interval_minutes`로 설정합니다 (기본 3분).
- 계좌번호는 하이픈 없이 10자리로 입력합니다 (예: "5012345601").
- 종료: `Ctrl+C`

## 커스텀 스킬

스터디원은 아래 슬래시 명령으로 Claude의 도움을 받을 수 있습니다:

- `/setup` — 처음 시작할 때. 환경 설정을 단계별로 안내합니다.
- `/new-strategy` — 새로운 매매 전략을 만들거나 기존 전략을 수정합니다.
- `/check` — config.yaml과 환경이 제대로 설정되었는지 검증합니다.
- `/deploy` — 서버에 Docker로 봇을 배포합니다.
