import os
import json
import httpx
from typing import List, Dict, Any
from config import settings
from utils.embeddings import get_embeddings
from utils.vector_store import VectorStore

class RAGService:
    def __init__(self):
        self.vector_store = VectorStore()
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.MODEL_NAME
        self.document_path = settings.DOCUMENT_PATH
        
    def load_all_documents(self) -> List[str]:
        """document 폴더의 모든 텍스트 파일을 로드하여 벡터 DB에 저장합니다."""
        loaded_files = []
        try:
            # 문서 폴더 내 모든 .txt 파일 검색
            for file_name in os.listdir(self.document_path):
                if not file_name.endswith('.txt'):
                    continue
                    
                file_path = os.path.join(self.document_path, file_name)
                collection_name = os.path.splitext(file_name)[0]
                
                # 파일 내용 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
                    
                if text_content:
                    # 벡터 DB 저장
                    self.vector_store.add_texts([text_content], collection_name)
                    loaded_files.append(file_name)
                    
            return loaded_files
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            return []

    async def query_ollama(self, prompt: str, stream: bool = False) -> str:
        try:
            # 타임아웃 설정 증가
            timeout = httpx.Timeout(
                timeout=120.0,     # 전체 타임아웃
                connect=30.0,     # 연결 타임아웃
                read=120.0,       # 읽기 타임아웃
                write=30.0,       # 쓰기 타임아웃
                pool=30.0         # 풀 타임아웃
            )
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": stream,
                        "system": "당신은 한국어 전용 답변 도우미입니다. 다음 규칙을 절대적으로 따르세요:\n1. 오직 한글로만 답변하세요\n2. 영어는 한글로 변환하세요 (API -> 에이피아이)\n3. 특수문자와 한자는 사용하지 마세요\n4. 간단명료하게 핵심만 답변하세요\n5. 모든 외래어는 한글로 표기하세요\n6. 답변 이외의 설명은 하지 마세요\n7. 생각하는 과정을 보여주지 마세요\n8. 바로 결과만 보여주세요"
                    }
                )

                if response.status_code != 200:
                    print(f"Error response from Ollama API: {response.text}")
                    return "⚠️ Ollama API 오류"
                
                if stream:
                    # 스트리밍 응답 처리
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                json_response = json.loads(line)
                                if 'response' in json_response:
                                    full_response += json_response['response']
                            except json.JSONDecodeError:
                                continue
                    
                    if not full_response:
                        return "⚠️ Ollama 응답 오류"
                    
                    response_text = full_response
                else:
                    # 단일 응답 처리
                    json_response = response.json()
                    if 'response' not in json_response:
                        return "⚠️ Ollama 응답 오류"
                    
                    response_text = json_response['response']
                
                # think 태그와 그 내용 제거
                if '<think>' in response_text:
                    parts = response_text.split('<think>')
                    for i in range(1, len(parts)):
                        if '</think>' in parts[i]:
                            parts[i] = parts[i].split('</think>', 1)[1]
                    response_text = ''.join(parts).strip()
                
                # 응답에서 '[' 로 시작하는 헤더 부분 제거
                if '[' in response_text:
                    response_text = response_text.split(']')[-1].strip()
                
                # 추가 개행 제거 및 포맷 정리
                lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                
                # 처음 줄은 그대로 유지하고, 번호 항목만 구분
                if not lines:
                    return "⚠️ 응답이 비어있습니다."
                    
                formatted_response = lines[0]
                for line in lines[1:]:
                    # 숫자로 시작하는 경우 (1. 2. 3. 등)
                    if line[0].isdigit() and len(line) > 1 and line[1] == '.':
                        formatted_response += '\n\n' + line
                    # 번호 리스트로 시작하는 경우 (1), 2), 3) 등)
                    elif line.startswith(('1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)')): 
                        formatted_response += '\n\n' + line
                    else:
                        formatted_response += '\n' + line
                
                return formatted_response
                
        except Exception as e:
            import traceback
            print(f"Error in query_ollama: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return "⚠️ Ollama API 오류"

    async def run_rag_query(self, collection_name: str, query: str, stream: bool = False) -> str:
        try:
            # 지정된 콜렉션의 문서 검색
            similar_docs = self.vector_store.similarity_search(collection_name, query)
            if not similar_docs:
                return "문서가 없습니다."
            
            # 프롬프트 생성
            # 검색된 문서를 구조화된 형태로 처리
            contexts = []
            for i, doc in enumerate(similar_docs, 1):
                if doc:
                    contexts.append(f"문서 {i}:\n{doc}")
            
            # 명확한 구분자로 문서들을 결합
            context = "\n\n=== 다음 문서 ===\n\n".join(contexts)
            
            # 프롬프트 구성
            prompt = f"""
다음 지시사항을 엄격히 따라 답변해주세요:

1. 반드시 한글로만 답변하세요.
2. 영어 단어는 모두 한글로 변환하세요 (예: API -> 에이피아이).
3. 특수문자나 한자는 절대 사용하지 마세요.
4. 간단명료하게 답변하세요.
5. 불필요한 설명이나 부연은 제외하세요.
6. 답변 전에 생각하는 과정을 보여주지 마세요.
7. 바로 결과만 보여주세요.

주어진 문서:
{context}

질문:
{query}

답변 형식:
[질문에 대한 답변만 작성]
"""
            # 프롬프트 출력 제거
            
            # Ollama API 호출
            response = await self.query_ollama(prompt, stream=stream)
            return response
            
        except Exception as e:
            import traceback
            print(f"Error in run_rag_query: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return "쿼리 처리 중 오류가 발생했습니다."
