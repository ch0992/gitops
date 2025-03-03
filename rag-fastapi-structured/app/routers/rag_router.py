from fastapi import APIRouter, HTTPException
from pathlib import Path
from schemas.rag import (
    LoadDocumentRequest, QueryRequest, QueryResponse,
    DeleteCollectionResponse, CollectionListResponse,
    CollectionContentsResponse, LoadAllResponse, DeleteAllResponse
)
from services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

# 1. Load API endpoints
@router.post("/documents", response_model=LoadAllResponse, tags=["1. Load"])
async def load_all_documents():
    """모든 텍스트 파일을 로드합니다."""
    try:
        loaded_files = rag_service.load_all_documents()
        return LoadAllResponse(loaded_files=loaded_files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/single", tags=["1. Load"])
async def load_document(request: LoadDocumentRequest):
    """텍스트 파일을 로드하여 벡터 DB에 저장합니다."""
    try:
        # 파일 경로 처리
        file_path = Path(rag_service.document_path) / request.file_path
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File '{request.file_path}' not found in '{rag_service.document_path}' directory"
            )
        
        # 콜렉션명이 비어있으면 파일명 사용
        collection_name = request.collection_name or file_path.stem
        
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
            
        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail=f"File '{request.file_path}' is empty"
            )
        
        # 벡터 DB 저장
        rag_service.vector_store.add_texts([text_content], collection_name)
        
        return {
            "message": "Document loaded and stored successfully",
            "collection_name": collection_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Collection API endpoints
@router.get("/collections", response_model=CollectionListResponse, tags=["2. Collections"])
async def list_collections():
    """모든 콜렉션 목록을 반환합니다."""
    try:
        collections = rag_service.vector_store.list_collections()
        return CollectionListResponse(collections=collections)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collections/{collection_name}", response_model=CollectionContentsResponse, tags=["2. Collections"])
async def get_collection_contents(collection_name: str):
    """콜렉션의 모든 문서를 조회합니다."""
    try:
        documents = rag_service.vector_store.get_collection_documents(collection_name)
        return CollectionContentsResponse(
            collection_name=collection_name,
            documents=documents,
            count=len(documents)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/collections/{collection_name}", response_model=DeleteCollectionResponse, tags=["2. Collections"])
async def delete_collection(collection_name: str):
    """지정된 콜렉션을 삭제합니다."""
    try:
        rag_service.vector_store.delete_collection(collection_name)
        return DeleteCollectionResponse(
            message="Collection deleted successfully",
            deleted_collection=collection_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/collections", response_model=DeleteAllResponse, tags=["2. Collections"])
async def delete_all_collections():
    """모든 콜렉션을 삭제합니다."""
    try:
        deleted = rag_service.vector_store.delete_all_collections()
        return DeleteAllResponse(deleted_collections=deleted)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Query API endpoints
@router.post("/query", response_model=QueryResponse, tags=["3. Query"])
async def process_query(request: QueryRequest):
    """콜렉션에서 쿼리에 대한 답변을 생성합니다."""
    try:
        # 콜렉션 존재 여부 확인
        collections = rag_service.vector_store.list_collections()
        if request.collection_name not in collections:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{request.collection_name}' not found"
            )
            
        
        # 콜렉션의 문서 가져오기
        documents = rag_service.vector_store.get_collection_documents(request.collection_name)
        if not documents:
            raise HTTPException(
                status_code=404,
                detail=f"No documents found in collection '{request.collection_name}'"
            )
        context = documents[0]  # 첫 번째 문서를 컨텍스트로 사용
        
        response = await rag_service.run_rag_query(request.collection_name, request.query, stream=request.stream)
        print(f"Response: {response}")
        
        return QueryResponse(response=response)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))
