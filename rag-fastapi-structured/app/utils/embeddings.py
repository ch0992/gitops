from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from config import settings

model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

def get_embeddings(texts: List[str]) -> List[float]:
    """
    텍스트 리스트를 입력받아 첫 번째 텍스트의 임베딩 벡터를 반환합니다.
    ChromaDB는 단일 임베딩을 바로 받을 수 있습니다.
    """
    embeddings = model.embed_documents(texts)
    return embeddings[0]  # 첫 번째 텍스트의 임베딩만 반환
