# Novel Processor 프로젝트

AI 기반 소설 생성 및 음악 추천 시스템

## 🚀 시작하기

### 1. 환경 설정

#### 환경변수 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# env.example 파일을 복사하여 시작
cp env.example .env
```

#### 필수 환경변수

`.env` 파일에서 다음 값들을 설정해야 합니다:

```bash
# OpenAI API 설정
OPENAI_API_KEY=your_actual_openai_api_key

# MongoDB 설정  
MONGODB_URL=mongodb://localhost:27017/novel_db
MONGODB_DATABASE=novel_db

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 모델 경로 설정
KOELECTRA_MODEL_PATH=outputs/koelectra_emotion
VECTOR_STORE_PATH=./vector_store

# 애플리케이션 설정
LOG_LEVEL=INFO
DEBUG=False
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

#### MongoDB 설치 및 실행

```bash
# Docker를 사용하는 경우
docker run -d -p 27017:27017 --name mongodb mongo:latest

# 또는 로컬 MongoDB 설치
# https://www.mongodb.com/try/download/community
```

#### Redis 설치 및 실행

```bash
# Docker를 사용하는 경우
docker run -d -p 6379:6379 --name redis redis:latest

# 또는 로컬 Redis 설치
# https://redis.io/download
```

### 4. 모델 다운로드

KoELECTRA 감정 분석 모델을 다운로드하고 `outputs/koelectra_emotion` 디렉토리에 배치하세요.

## 🔒 보안 주의사항

### 중요한 파일들

다음 파일들은 **절대 Git에 커밋하지 마세요**:

- `.env` - 실제 API 키와 민감한 설정 포함
- `*.log` - 로그 파일에 민감한 정보가 포함될 수 있음
- `outputs/` - 모델 파일들 (크기가 크고 때로는 민감함)
- `vector_store/` - 벡터 저장소 파일들

### API 키 관리

1. **OpenAI API 키**: [OpenAI 플랫폼](https://platform.openai.com/api-keys)에서 발급
2. **MongoDB URL**: 프로덕션 환경에서는 인증이 포함된 연결 문자열 사용
3. **환경별 설정**: 개발/스테이징/프로덕션별로 다른 `.env` 파일 사용

## 📂 프로젝트 구조

```
src/
├── src/
│   ├── api/
│   │   ├── gpt_client.py      # OpenAI GPT 클라이언트
│   │   └── rag_client.py      # RAG 벡터 검색 클라이언트
│   ├── database/
│   │   └── db_manager.py      # MongoDB 데이터베이스 관리
│   ├── utils/
│   │   ├── emotion_analyzer.py    # KoELECTRA 감정 분석
│   │   ├── music_recommender.py   # 음악 추천 시스템
│   │   ├── prompt_templates.py    # GPT 프롬프트 템플릿
│   │   └── text_processor.py      # 텍스트 처리 유틸리티
│   └── main.py                # 메인 애플리케이션 로직
├── env.example               # 환경변수 예시 파일
├── .gitignore               # Git 무시 파일 목록
└── README.md               # 이 파일
```

## 🔧 사용법

### 챕터 생성

```python
from src.main import process_job

result = process_job(
    "generate_chapter",
    user_id="user123",
    user_message="주인공이 모험을 시작합니다.",
    book_id="book456"
)
```

### 음악 추천

```python
result = process_job(
    "recommendate_music",
    user_id="user123",
    book_id="book456"
)
```

## 🚨 트러블슈팅

### 환경변수 오류

```
ValueError: OpenAI API key is required
```

→ `.env` 파일에 `OPENAI_API_KEY`가 설정되어 있는지 확인

### MongoDB 연결 오류

```
Failed to connect to MongoDB
```

→ MongoDB가 실행 중인지 확인하고 `MONGODB_URL`이 올바른지 검사

### Redis 연결 오류

```
ConnectionError: Error connecting to Redis
```

→ Redis 서버가 실행 중인지 확인하고 Redis 설정 검토

## 📝 개발자 노트

### 환경변수 추가 시

1. `env.example` 파일에 새 변수 추가
2. 해당 코드에서 `os.getenv()` 사용
3. README.md 업데이트
4. 기본값 설정 권장

### 새로운 API 키 추가 시

1. 환경변수로 관리
2. `.gitignore`에 관련 파일 추가
3. 초기화 시 검증 로직 추가

## 🤝 기여하기

1. 민감한 정보는 절대 커밋하지 마세요
2. 새로운 환경변수는 `env.example`에 추가
3. 보안 관련 변경사항은 README 업데이트 