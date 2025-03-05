#!/bin/bash

# 이미지 및 레지스트리 설정
IMAGE_NAME="rag-fastapi-structured"
REGISTRY="localhost:5000"
VALUES_FILE="./helm/values-local.yaml"

# 현재 values-local.yaml에서 tag 값 가져오기 (숫자 태그만 대상)
CURRENT_TAG=$(grep -Eo 'tag: [0-9]+' "$VALUES_FILE" | awk '{print $2}')

# 태그 값이 없거나 숫자가 아니면 기본값 1 설정
if [[ -z "$CURRENT_TAG" ]]; then
    NEW_TAG=1
else
    NEW_TAG=$((CURRENT_TAG + 1))
fi

# Docker 이미지 빌드 (`latest`만 사용)
echo "🚀 Building new image: $IMAGE_NAME:latest"
docker build -t $IMAGE_NAME:latest .
echo "✅ Built and tagged image: $IMAGE_NAME:latest"

# 로컬 레지스트리에 `latest` 푸시
docker tag $IMAGE_NAME:latest $REGISTRY/$IMAGE_NAME:latest
echo "🚀 Pushing latest image to local registry..."
docker push $REGISTRY/$IMAGE_NAME:latest
echo "✅ Pushed latest image to $REGISTRY"

# values-local.yaml에서 tag 값을 증가된 값으로 업데이트 (Helm이 변경 사항 감지)
sed -i.bak "s/tag: .*/tag: $NEW_TAG/" "$VALUES_FILE"
echo "✅ Updated values-local.yaml with tag: $NEW_TAG"

# # Git 커밋 & 푸시 (ArgoCD가 변경 감지)
# git add "$VALUES_FILE"
# git commit -m "Update image tag to $NEW_TAG"
# git push origin main
# echo "✅ Pushed values-local.yaml update to Git"

# # ArgoCD 동기화
# echo "🚀 Syncing ArgoCD Application..."
# argocd app sync rag-fastapi-local
# echo "✅ ArgoCD sync complete!"

# 최신 Docker 이미지 목록 확인
echo "🔍 Remaining Docker Images for $IMAGE_NAME:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep $IMAGE_NAME