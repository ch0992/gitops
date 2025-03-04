#!/bin/bash

# 이미지 이름 및 Helm values 파일 설정
IMAGE_NAME="rag-fastapi-structured"
VALUES_FILE="./helm/values-local.yaml"

# 현재 로컬에 존재하는 해당 이미지의 태그 목록 가져오기 (숫자로 된 태그만 필터링)
LATEST_TAG=$(docker images --format "{{.Tag}}" $IMAGE_NAME | grep -E '^[0-9]+$' | sort -nr | head -n1)

# 태그가 없으면 1부터 시작, 있으면 1 증가
if [[ -z "$LATEST_TAG" ]] || [[ "$LATEST_TAG" == "latest" ]]; then
    NEW_TAG=1
else
    NEW_TAG=$((LATEST_TAG + 1))
fi

# Docker 이미지 빌드 및 태깅
docker build -t $IMAGE_NAME:$NEW_TAG .
echo "✅ Built and tagged image: $IMAGE_NAME:$NEW_TAG"

# values-local.yaml 파일에서 tag 값 업데이트
if [[ -f "$VALUES_FILE" ]]; then
    sed -i.bak "s/tag: .*/tag: $NEW_TAG/" "$VALUES_FILE"
    echo "✅ Updated $VALUES_FILE with tag: $NEW_TAG"
else
    echo "⚠️ Error: $VALUES_FILE not found!"
    exit 1
fi

# 기존의 오래된 이미지 삭제 (latest 제외)
echo "🗑️ Cleaning up old images..."
docker images --format "{{.Repository}}:{{.Tag}}" | grep "$IMAGE_NAME:" | grep -v "$NEW_TAG" | xargs -r docker rmi -f

# 빌드 완료 후 최신 Docker 이미지 목록 확인
echo "🔍 Docker Images for $IMAGE_NAME:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | grep $IMAGE_NAME