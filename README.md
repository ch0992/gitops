# GitOps Project

## 프로젝트 개요

이 프로젝트는 ArgoCD를 사용하여 RAG(Retrieval-Augmented Generation) FastAPI 애플리케이션을 Kubernetes 클러스터에 배포하는 GitOps 구현체입니다.
두 가지 배포 환경을 제공합니다:

1. Local 환경: 로컬에서 이미지를 빌드하고 ArgoCD를 통해 배포
2. GitHub 환경: GitHub Actions와 GitHub Container Registry를 사용한 자동화된 배포

## 프로젝트 구조

```
gitops/
├── rag-fastapi-structured/    # 공유 애플리케이션 코드
│   ├── helm/                # Helm 차트
│   └── Dockerfile           # 컨테이너 이미지 설정
│
├── local/                     # 로컬 환경 배포
│   └── argocd/               # 로컬용 ArgoCD 설정
│       └── application.yaml # ArgoCD 애플리케이션 정의
│
├── github/                   # GitHub 환경 배포
│   ├── .github/workflows/   # GitHub Actions 워크플로우
│   └── argocd/              # GitHub용 ArgoCD 설정
│       └── application.yaml # ArgoCD 애플리케이션 정의
│
└── secret/                   # 공통 시크릿 템플릿
```

## 배포 환경

### 1. Local 환경
- 로컬에서 Docker 이미지 빌드
- 로컬 이미지를 사용하여 배포
- Git 저장소를 통한 매니페스트 관리
- ArgoCD를 통한 배포 자동화

### 2. GitHub 환경 (준비 중)
- GitHub Actions를 통한 CI/CD 파이프라인
- GitHub Container Registry를 통한 이미지 관리
- Git 저장소를 통한 매니페스트 관리
- ArgoCD를 통한 배포 자동화

## 시크릿 관리

시크릿은 공통 템플릿을 사용하여 환경별로 관리됩니다.

### 1. 시크릿 설정

1) `.env` 파일 생성 
```bash
echo "GIT_REPO_URL={git repository address}" >> .env
echo "GIT_USERNAME={username}" >> .env
echo "GIT_PASSWORD={password or access token}" >> .env
```

2) 환경변수 로드
```bash
export $(grep -v '^#' .env | xargs)
```

3) ArgoCD Repository Secret 생성
```bash
# Secret 템플릿 생성
envsubst < ../secret/argocd-repository-template.yaml > ../secret/argocd-repository.yaml

# Secret 적용
kubectl apply -f ../secret/argocd-repository.yaml

# Secret 확인
kubectl get secrets -n argocd | grep argocd-repo-gitops-local
```

### 2. Docker 이미지 빌드
```bash
cd rag-fastapi-structured
docker build -t rag-fastapi-structured .
```

### 3. ArgoCD 로그인
```bash
argocd login http://localhost:8070 --username {username} --password {password} --insecure
```

### 4. 애플리케이션 배포

1) Application 등록
```bash
kubectl apply -f ./local/argocd/argocd-application.yaml
```

2) 배포 상태 확인
```bash
argocd app get rag-fastapi
```

3) 문제 해결

배포 실패 시:
```bash
# 수동 동기화
argocd app sync rag-fastapi

# 필요시 애플리케이션 삭제
argocd app delete rag-fastapi
```

## GitHub 환경 배포 가이드

### 2. 시크릿 설정

1) `.env` 파일 생성 
```bash
echo "GIT_REPO_URL={git repository url}" >> .env
echo "GIT_USERNAME={github username}" >> .env
echo "GIT_PASSWORD={github personal access token}" >> .env

```

2) 환경변수 로드
```bash
export $(grep -v '^#' .env | xargs)

# GitHub Container Registry 로그인
docker login ghcr.io -u ${GIT_USERNAME} -p ${GIT_PASSWORD}

# Docker config.json을 base64로 인코딩
echo "DOCKER_CONFIG_JSON=$(cat ~/.docker/config.json | base64)" >> .env

```

3) ArgoCD Repository Secret 생성
```bash
# Secret 템플릿 생성
envsubst < ./secret/argocd-repository-template.yaml > ./secret/argocd-repository.yaml

# Secret 적용
kubectl apply -f ./secret/argocd-repository.yaml

# Secret 확인
kubectl get secrets -n argocd | grep 'argocd-repo-gitops-github\|ghcr-secret'
```

2) Application 등록
```bash
# Application 템플릿에 환경변수 적용
envsubst < ./github/argocd/application.yaml | kubectl apply -f -
```

### 3. 배포 확인

1) GitHub Actions 상태 확인
- GitHub repository의 Actions 탭에서 워크플로우 상태를 확인합니다.

2) ArgoCD 상태 확인
```bash
argocd app get rag-fastapi-github
```

### 4. 자동화된 배포 흐름

1. GitHub에 코드 push
2. GitHub Actions에서 자동으로:
   - Docker 이미지 빌드
   - GitHub Container Registry에 이미지 push
3. ArgoCD가 자동으로:
   - 새로운 이미지 감지
   - 클러스터에 업데이트된 이미지 배포

## 애플리케이션 구성

### 리소스 설정
- CPU: 1000m (limit), 500m (request)
- Memory: 2Gi (limit), 1Gi (request)

### 헬스체크
- Liveness Probe: 2분 초기 지연, 30초 간격
- Readiness Probe: 1분 초기 지연, 5초 간격, 12회 재시도

## 주의사항

1. Git 인증 정보는 반드시 안전하게 관리해야 합니다.
2. ArgoCD Application을 삭제하기 전에 관련 리소스가 정리되었는지 확인하세요.
3. 프로덕션 환경에서는 적절한 리소스 설정과 보안 정책을 적용해야 합니다.