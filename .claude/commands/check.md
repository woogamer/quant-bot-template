# 설정 검증

config.yaml과 환경 설정이 올바른지 검증해주세요.

## 검증 항목

아래 항목을 순서대로 확인하고 결과를 알려주세요.

### 1. Python 버전
- `python --version` 실행하여 3.10 이상인지 확인

### 2. 패키지 설치 여부
- `requirements.txt`에 있는 패키지들이 설치되어 있는지 확인
- `python -c "import requests; import schedule; import yaml; import telegram; print('OK')"` 실행

### 3. config.yaml 존재 여부
- `config.yaml` 파일이 있는지 확인
- 없으면 `cp config.template.yaml config.yaml` 안내

### 4. config.yaml 구조 검증
- config.yaml을 읽어서 아래 필드가 모두 존재하고 기본 템플릿 값이 아닌지 확인:
  - `kis.app_key` — 비어있거나 "YOUR_APP_KEY"가 아닌지
  - `kis.app_secret` — 비어있거나 "YOUR_APP_SECRET"가 아닌지
  - `kis.account_no` — "12345678-01"이 아닌지, 형식이 맞는지 (숫자8자리-숫자2자리)
  - `telegram.bot_token` — 비어있거나 예시값이 아닌지
  - `telegram.chat_id` — 0이 아닌지, 정수인지

### 5. my_strategy.py 검증
- `generate_signal` 함수가 존재하는지
- `WATCHLIST`가 정의되어 있고 종목코드가 들어있는지

## 출력 형식

각 항목을 체크리스트로 보여주세요:

```
[OK] Python 3.12.0
[OK] 패키지 설치 완료
[OK] config.yaml 존재
[OK] KIS API 키 설정됨
[OK] 텔레그램 설정됨
[OK] 전략 파일 정상
```

문제가 있는 항목은 `[!!]`로 표시하고 해결 방법을 안내하세요.

**주의: config.yaml의 실제 키 값을 터미널에 절대 출력하지 마세요. 존재 여부와 형식만 확인하세요.**
