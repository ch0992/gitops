#!/bin/bash

# 이미지 이름 및 Helm values 파일 설정
IMAGE_NAME="rag-fastapi-structured"
VALUES_FILE="./helm/values-local.yaml"

# 최신 태그 생성 (YYYYMMDDHHMMSS 형식)
NEW_TAG=$(date +%Y%m%d%H%M%S)

# 기존 latest 태그가 참조하는 이미지 ID 가져오기
EXISTING_LATEST_IMAGE_ID=$(docker images -q $IMAGE_NAME:latest)

# 기존 latest 및 참조 이미지 삭제 (존재하는 경우)
if [[ -n "$EXISTING_LATEST_IMAGE_ID" ]]; then
    echo "🗑️ Removing existing latest tag and its referenced image ($EXISTING_LATEST_IMAGE_ID)..."
    docker rmi -f $IMAGE_NAME:latest
    docker rmi -f $EXISTING_LATEST_IMAGE_ID
fi

# 기존에 존재하는 동일한 이름의 모든 이미지 삭제
echo "🗑️ Removing all old images of $IMAGE_NAME..."
docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | grep "$IMAGE_NAME:" | awk '{print $1}' | xargs -r docker rmi -f

# Docker 이미지 빌드 (캐시 사용 안함, 베이스 이미지 강제 다운로드)
docker build --no-cache --pull -t $IMAGE_NAME:$NEW_TAG .
echo "✅ Built and tagged image: $IMAGE_NAME:$NEW_TAG"

# 새로 생성된 날짜 태그를 latest로 다시 태깅
docker tag $IMAGE_NAME:$NEW_TAG $IMAGE_NAME:latest
echo "✅ Tagged $IMAGE_NAME:$NEW_TAG as latest"

# values-local.yaml 파일에서 tag 값을 latest로 업데이트
if [[ -f "$VALUES_FILE" ]]; then
    sed -i.bak "s/tag: .*/tag: latest/" "$VALUES_FILE"
    echo "✅ Updated values-local.yaml with tag: latest"
else
    echo "⚠️ Error: values-local.yaml not found!"
    exit 1
fi

# 최신 Docker 이미지 목록 확인 (2개만 유지: latest, 최신 날짜 태그)
echo "🔍 Remaining Docker Images for $IMAGE_NAME:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep $IMAGE_NAME
