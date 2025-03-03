import os
from fastapi import FastAPI
from routers import rag_router
from services.rag_service import RAGService
from config import settings

app = FastAPI(
    title="RAG API",
    description="사용자 쿼리에 대한 답변을 생성하는 RAG(Retrieval-Augmented Generation) API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# API 라우터 등록
app.include_router(
    rag_router.router,
    prefix="/api/v1"
)

# 시작 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 문서 폴더를 초기화하고 문서를 로드합니다."""
    try:
        # document 폴더 경로 가져오기
        if not os.path.exists(settings.DOCUMENT_PATH):
            os.makedirs(settings.DOCUMENT_PATH)
            print(f"Created document directory at: {settings.DOCUMENT_PATH}")
        
        # 문서 자동 로드
        rag_service = RAGService()
        loaded_files = rag_service.load_all_documents()
        if loaded_files:
            print("\n📄 Document Loading Status:")
            print("-" * 30)
            for file in loaded_files:
                print(f"  ✓ {file}")
            print(f"  Total: {len(loaded_files)} documents loaded\n")
        else:
            print("\n⚠️ No documents found to load\n")
            
        print("🟢 Server started successfully")
            
    except Exception as e:
        print(f"Error during startup: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to RAG API",
        "docs": "/docs",
        "version": "1.0.0"
    }
