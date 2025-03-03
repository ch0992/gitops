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

### 1. 환경별 설정 및 시크릿 생성

1) Local 환경 `.env` 파일 생성
```bash
# 공통 환경변수 설정
echo "GIT_REPO_URL={git repository url}" > .env
echo "GIT_USERNAME={github username}" >> .env
echo "GIT_PASSWORD={github personal access token}" >> .env

# Local 환경 설정
echo "ENV=local" >> .env
```

2) GitHub 환경 `.env` 파일 생성
```bash
# 공통 환경변수 설정
echo "GIT_REPO_URL={git repository url}" > .env
echo "GIT_USERNAME={github username}" >> .env
echo "GIT_PASSWORD={github personal access token}" >> .env

# GitHub 환경 설정
echo "ENV=github" >> .env
echo "GITHUB_USERNAME={github username}" >> .env

# GitHub Container Registry 로그인
docker login ghcr.io -u ${GIT_USERNAME} -p ${GIT_PASSWORD}

# Docker config.json을 base64로 인코딩
echo "DOCKER_CONFIG_JSON=$(cat ~/.docker/config.json | base64)" >> .env
```

3) 환경변수 로드
```bash
export $(grep -v '^#' .env | xargs)
```

4) 시크릿 생성

4.1) ArgoCD Repository Secret 생성
```bash
# Secret 템플릿 생성
envsubst < ./secret/argocd-repository-template.yaml > ./secret/argocd-repository.yaml

# Secret 적용
kubectl apply -f ./secret/argocd-repository.yaml

# Secret 확인
kubectl get secrets -n argocd | grep 'argocd-repo-gitops'
```

4.2) GitHub Container Registry Secret 생성 (GitHub 환경)
```bash
# GitHub Container Registry 로그인
docker login ghcr.io -u ${GIT_USERNAME} -p ${GIT_PASSWORD}

# 시크릿 생성
kubectl create namespace fastapi
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=${GIT_USERNAME} \
  --docker-password=${GIT_PASSWORD} \
  -n fastapi

# 서비스 계정에 시크릿 연결
kubectl patch serviceaccount default -n fastapi \
  -p '{"imagePullSecrets": [{"name": "ghcr-secret"}]}'

# Secret 확인
kubectl get secrets -n fastapi | grep 'ghcr-secret'
```

### 2. 애플리케이션 배포

#### Local 환경 배포

1) Docker 이미지 빌드
```bash
# rag-fastapi-structured 디렉토리로 이동
cd rag-fastapi-structured

# 이미지 빌드
docker build -t rag-fastapi-structured:latest .
```

2) ArgoCD 로그인
```bash
argocd login http://localhost:8070 --username {username} --password {password} --insecure
```

3) Application 등록
```bash
# Application 생성
kubectl apply -f ./local/argocd/application.yaml

# 배포 상태 확인
argocd app get rag-fastapi-local

# 리소스 확인
kubectl get all,ingress -n fastapi -l app=rag-fastapi-local
```

4) 서비스 접근
```bash
# API 테스트
curl localhost:8000

# Swagger UI 접근
open http://localhost:8000/docs
```

#### GitHub 환경 배포

1) GitHub Container Registry 이미지 준비
```bash
# 이미지 빌드
docker build -t ghcr.io/ch0992/rag-fastapi-structured:latest ./rag-fastapi-structured

# GitHub Container Registry 로그인
docker login ghcr.io -u ${GIT_USERNAME} -p ${GIT_PASSWORD}

# 이미지 푸시
docker push ghcr.io/ch0992/rag-fastapi-structured:latest
```

2) Application 등록
```bash
# Application 생성
kubectl apply -f ./github/argocd/application.yaml

# 배포 상태 확인
argocd app get rag-fastapi-github

# 리소스 확인
kubectl get all,ingress -n fastapi -l app=rag-fastapi-github
```

3) 서비스 접근
```bash
# API 테스트
curl localhost:8001

# Swagger UI 접근
open http://localhost:8001/docs
```

### 3. 트러블슈팅 가이드

#### 1. ArgoCD Repository Secret 문제

증상:
- ArgoCD에서 Git 저장소에 접근하지 못하는 경우
- `ComparisonError: failed to generate manifest` 에러 발생

해결방법:
```bash
# 1. Secret 존재 여부 확인
kubectl get secrets -n argocd | grep 'argocd-repo-gitops'

# 2. Secret 재생성
envsubst < ./secret/argocd-repository-template.yaml > ./secret/argocd-repository.yaml
kubectl apply -f ./secret/argocd-repository.yaml

# 3. Application 재동기화
argocd app sync rag-fastapi-local
```

#### 2. GitHub Container Registry 인증 문제

증상:
- `ImagePullBackOff` 또는 `ErrImagePull` 에러
- `unauthorized: authentication required` 메시지

해결방법:
```bash
# 1. GitHub Container Registry Secret 생성
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=${GIT_USERNAME} \
  --docker-password=${GIT_PASSWORD} \
  -n fastapi

# 2. 서비스 계정에 Secret 연결
kubectl patch serviceaccount default -n fastapi \
  -p '{"imagePullSecrets": [{"name": "ghcr-secret"}]}'

# 3. Pod 재시작
kubectl delete pod -n fastapi -l app=rag-fastapi-github
```

#### 3. 서비스 포트 충돌

증상:
- Local과 GitHub 환경의 서비스가 같은 포트(8000)를 사용하려고 할 때

해결방법:
```bash
# 1. GitHub 환경의 서비스 포트를 8001로 변경
# github/argocd/application.yaml 파일의 values 섹션에 추가:
service:
  port: 8001

# 2. 변경사항 적용
kubectl apply -f ./github/argocd/application.yaml

# 3. 서비스 포트 확인
kubectl get svc -n fastapi
```

#### 4. 애플리케이션 재배포

문제가 지속되는 경우 전체 재배포:
```bash
# 1. 애플리케이션 삭제
argocd app delete rag-fastapi-local  # 또는 rag-fastapi-github

# 2. 리소스 정리 확인
kubectl get all,ingress -n fastapi

# 3. 애플리케이션 재생성
kubectl apply -f ./local/argocd/application.yaml  # 또는 ./github/argocd/application.yaml
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