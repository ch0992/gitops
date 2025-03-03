# RAG Lab - Structured FastAPI Implementation

이 프로젝트는 Ollama와 ChromaDB를 사용하는 한국어 특화 RAG(Retrieval-Augmented Generation) 시스템의 구조적 구현입니다. FastAPI의 구조화된 아키텍처를 따르며, 확장 가능하고 유지보수가 용이한 문서 기반 질의응답 서비스를 제공합니다.

## 기능

- 문서 기반 질의응답
- ChromaDB를 이용한 벡터 저장소
- 임베딩 기반 문서 검색
- Ollama를 이용한 응답 생성
- 다중 문서 컬렉션 지원

## 설치 및 실행

1. Python 가상환경 생성 및 활성화:
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Mac/Linux
# 또는
venv\Scripts\activate  # Windows
```

2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. Ollama 설치 및 실행:
```bash
# Ollama 설치 (Mac)
brew install ollama

# Ollama 실행
ollama run deepseek-coder
```

4. 환경 설정:
기본 환경 변수가 설정되어 있으며, 필요시 다음 값들을 변경할 수 있습니다:

```python
# config.py 기본값
OLLAMA_BASE_URL: str = "http://localhost:11434"
MODEL_NAME: str = "deepseek-r1:8b"
EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DOCUMENT_PATH: str = "./document"
PERSIST_DIR: str = "./data"  # ChromaDB 데이터 영구 저장 경로
```

5. 서버 실행:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 엔드포인트

모든 엔드포인트는 `/api/v1` 접두사를 사용합니다.

### 1. 문서 관리
- `POST /upload`: 문서 업로드 및 벡터 DB 저장
- `POST /load`: 기존 문서 로드 및 벡터 DB 저장

### 2. 컬렉션 관리
- `GET /collections`: 모든 컬렉션 목록 조회
- `GET /collections/{collection_name}`: 특정 컬렉션 조회
- `DELETE /collections/{collection_name}`: 특정 컬렉션 삭제

### 3. 질의응답
- `POST /query`: RAG 기반 질의응답

## 프로젝트 구조

```
rag-fastapi-structured/
├── app/
│   ├── config.py           # 환경 변수 및 설정
│   ├── main.py            # FastAPI 애플리케이션 진입점
│   ├── data/              # ChromaDB 데이터 저장소
│   ├── document/          # 문서 파일 저장소
│   ├── routers/           # API 엔드포인트 정의
│   │   └── rag_router.py  # RAG 관련 라우터
│   ├── schemas/           # API 요청/응답 스키마
│   │   └── rag.py        # RAG 관련 스키마
│   ├── services/          # 비즈니스 로직
│   │   └── rag_service.py # RAG 서비스 구현
│   └── utils/             # 유틸리티
│       ├── embeddings.py  # 임베딩 모델 설정
│       └── vector_store.py # 벡터 저장소 구현
└── README.md
```

## 주요 컴포넌트

### 1. 벡터 저장소 (VectorStore)
- ChromaDB 기반 구현
- 문서의 벡터 임베딩 저장 및 검색
- 다중 컬렉션 지원

### 2. RAG 서비스
- 문서 로딩 및 관리
- 벡터 검색 기반 관련 문서 검색
- Ollama API를 통한 응답 생성

### 3. API 라우터
- RESTful API 엔드포인트 제공
- 에러 처리 및 응답 포맷팅
- 최소화된 로깅

## API 사용 예제

```bash
# 문서 업로드
curl -X POST http://localhost:8000/api/v1/upload \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/document.txt"

# 질의응답
curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"collection_name":"document","query":"질문내용"}'

# 컬렉션 목록 조회
curl http://localhost:8000/api/v1/collections
```

## 특징

- FastAPI의 구조화된 아키텍처 적용
  * 라우터, 서비스, 스키마 분리
  * 의존성 주입 패턴 사용
  * 타입 힌트 및 Pydantic 모델 활용

- 성능 최적화
  * 비동기 처리
  * 효율적인 벡터 검색
  * 응답 캐싱

- 확장성
  * 모듈화된 구조
  * 설정 중앙화
  * 유연한 컴포넌트 교체
