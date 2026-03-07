# 서버 배포 가이드

quant-bot-template을 서버에서 24시간 자동으로 돌리는 방법을 안내해주세요.

## 사전 조건 확인

먼저 사용자에게 물어보세요:
- 서버가 이미 있는지 (AWS, GCP, 개인 서버 등)
- Docker가 설치되어 있는지

## Docker 배포 (추천)

### 1단계: 서버에 프로젝트 올리기

```bash
# 서버에서 레포 클론
git clone <레포 URL>
cd quant-bot-template
```

### 2단계: config.yaml 설정

```bash
cp config.template.yaml config.yaml
# config.yaml을 편집하여 API 키, 텔레그램 설정 입력
```

### 3단계: 봇 실행

```bash
# 백그라운드로 봇 실행
docker compose up -d --build
```

### 자주 쓰는 명령

사용자에게 아래 명령들을 안내하세요:

```bash
# 로그 확인
docker compose logs -f

# 봇 중지
docker compose down

# 전략 수정 후 재시작
docker compose restart bot

# 봇 상태 확인
docker compose ps
```

## 전략 업데이트 방법

서버에서 전략을 바꾸는 두 가지 방법을 안내하세요:

1. **서버에서 직접 수정**: `my_strategy.py`를 편집한 뒤 `docker compose restart bot`
2. **로컬에서 수정 후 배포**: 로컬에서 전략 수정 → git push → 서버에서 `git pull && docker compose restart bot`

`my_strategy.py`는 Docker 볼륨으로 마운트되어 있어서 이미지 재빌드 없이 `restart`만 하면 됩니다.

## 안내 방식

- 사용자의 서버 환경에 맞게 안내하세요
- Docker가 없으면 설치 방법부터 안내하세요
- 각 단계를 하나씩 확인하며 진행하세요
