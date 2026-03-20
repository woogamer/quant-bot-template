# 환경 설정 가이드

quant-bot-template 초기 설정을 도와주세요. 아래 단계를 순서대로 안내하되, 사용자가 이미 완료한 단계는 건너뛰세요.

## 단계 1: Python 확인

터미널에서 `python --version` (또는 `python3 --version`)을 실행하여 Python 3.10 이상이 설치되어 있는지 확인하세요.
설치되어 있지 않으면 https://www.python.org/downloads/ 에서 설치하도록 안내하세요.
Windows 사용자라면 설치 시 "Add Python to PATH" 체크를 반드시 하라고 알려주세요.

## 단계 2: 패키지 설치

`pip install -r requirements.txt`를 실행하세요.

## 단계 3: KIS 모의투자 API 키 발급

사용자에게 아래를 안내하세요:
1. https://apiportal.koreainvestment.com/ 접속
2. 회원가입 후 로그인
3. "API 신청" 메뉴에서 **모의투자** API 신청
4. 앱 키(app_key)와 시크릿 키(app_secret) 확인
5. 모의투자 계좌번호 확인 (8자리 + 2자리, 예: 50112345 + 01)

## 단계 4: 알림 설정 (Telegram 또는 Slack 중 택 1 이상)

### Telegram (선택)
1. 텔레그램에서 @BotFather 검색하여 대화 시작
2. `/newbot` 명령 전송
3. 봇 이름과 username 설정
4. 발급된 봇 토큰(bot_token) 저장
5. 본인의 chat_id 확인: @userinfobot 에게 아무 메시지를 보내면 알려줌

### Slack (선택)
1. https://api.slack.com/apps 접속
2. Create New App → From scratch → 앱 이름/워크스페이스 선택
3. 왼쪽 메뉴 Incoming Webhooks → Activate 켜기
4. Add New Webhook to Workspace → 채널 선택 → Allow
5. Webhook URL 복사 (https://hooks.slack.com/services/... 형태)

## 단계 5: config.yaml 생성

`config.template.yaml`을 복사하여 `config.yaml`을 만들고, 위에서 발급받은 값들을 입력하세요.

```bash
cp config.template.yaml config.yaml
```

config.yaml을 직접 열어서 편집해주세요. 각 필드:
- `kis.app_key`: KIS 앱 키
- `kis.app_secret`: KIS 시크릿 키
- `kis.account_no`: 모의투자 계좌번호 (**하이픈 없이 10자리**, 예: "5012345601")
- `telegram.bot_token`: 텔레그램 봇 토큰 (Telegram 사용 시)
- `telegram.chat_id`: 본인 chat_id 정수 (Telegram 사용 시)
- `slack.webhook_url`: Slack Webhook URL (Slack 사용 시)

**주의: config.yaml에 실제 키 값을 넣은 뒤에도 절대 터미널에 내용을 출력하지 마세요.**

## 단계 6: 설정 검증

`/check` 명령을 실행하여 설정이 올바른지 확인하도록 안내하세요.

## 단계 7: 첫 실행

```bash
python main.py
```

Telegram/Slack으로 "봇 시작" 알림이 오면 성공입니다!
장 시간(09:00~15:30)이 아니면 전략은 실행되지 않지만, 시작 알림은 정상적으로 옵니다.

## 안내 방식

- 각 단계를 하나씩 진행하세요. 한꺼번에 다 보여주지 마세요.
- 사용자가 각 단계를 완료했는지 확인한 후 다음으로 넘어가세요.
- 에러가 발생하면 원인을 파악하고 해결을 도와주세요.
- 친절하고 쉬운 한국어로 설명하세요.
