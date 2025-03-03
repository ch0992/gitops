from pydantic import BaseModel
from typing import List, Optional

class LoadDocumentRequest(BaseModel):
    file_path: str = "sample.txt"  # document 폴더 내 파일명
    collection_name: str = ""  # 비어있으면 파일명이 콜렉션명으로 사용됨

class QueryRequest(BaseModel):
    collection_name: str
    query: str
    stream: bool = False

class QueryResponse(BaseModel):
    response: str

class DeleteCollectionResponse(BaseModel):
    message: str
    deleted_collection: str

class CollectionListResponse(BaseModel):
    collections: List[str]

class CollectionContentsResponse(BaseModel):
    collection_name: str
    documents: List[str]
    count: int

class LoadAllResponse(BaseModel):
    loaded_files: List[str]

class DeleteAllResponse(BaseModel):
    deleted_collections: List[str]
