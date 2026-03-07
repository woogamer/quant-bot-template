# 새 매매 전략 만들기

사용자가 원하는 매매 전략을 `my_strategy.py`에 구현해주세요.

## 진행 방식

1. 먼저 현재 `my_strategy.py`를 읽어서 기존 전략을 파악하세요.
2. 사용자에게 어떤 전략을 원하는지 물어보세요. 예시를 제안해도 좋습니다:
   - "삼성전자가 7만원 이하면 매수, 8만원 이상이면 매도"
   - "전일 대비 3% 이상 하락한 종목 매수"
   - "보유 종목이 10% 수익이면 매도"
   - "예수금의 10% 이내로만 매수"
3. 사용자의 요구사항을 `generate_signal()` 함수 내부에 구현하세요.
4. 필요하면 `WATCHLIST`에 종목을 추가하세요.

## 규칙

- `generate_signal(market_data, account_data) -> list[dict]` 시그니처는 절대 변경 금지
- 반환값 형식을 반드시 지키세요:
  ```python
  [{"ticker": "005930", "action": "BUY", "qty": 1, "price": 0}]
  ```
- `core/` 폴더와 `main.py`는 수정 금지
- 동기(synchronous) 코드만 사용
- 외부 패키지가 필요하면 사용자에게 `pip install`을 안내하고 `requirements.txt`에도 추가
- 한국어 주석으로 전략 로직을 설명해주세요

## 사용 가능한 데이터

### market_data (종목별 현재가)
```python
market_data["005930"]["현재가"]    # int, 현재 주가
market_data["005930"]["전일대비"]  # int, 전일 대비 가격 변동
market_data["005930"]["등락률"]    # float, 전일 대비 등락률 (%)
```

### account_data (계좌 잔고)
```python
account_data["예수금"]              # int, 주문 가능 금액
account_data["보유종목"]            # list[dict], 보유 종목 리스트
account_data["보유종목"][0]["종목코드"]  # str
account_data["보유종목"][0]["종목명"]    # str
account_data["보유종목"][0]["수량"]      # int
account_data["보유종목"][0]["평균단가"]  # int
```
