#!/bin/bash

# 이미지 이름 및 Helm values 파일 설정
IMAGE_NAME="rag-fastapi-structured"
VALUES_FILE="./helm/values-local.yaml"

# 최신 태그 생성 (YYYYMMDDHHMMSS 형식)
NEW_TAG=$(date +%Y%m%d%H%M%S)

# Docker 이미지 빌드 및 태깅
docker build -t $IMAGE_NAME:$NEW_TAG .
echo "✅ Built and tagged image: $IMAGE_NAME:$NEW_TAG"

# 기존의 latest 태그가 존재하면 새로운 태그로 업데이트
EXISTING_LATEST=$(docker images -q $IMAGE_NAME:latest)
if [[ -n "$EXISTING_LATEST" ]]; then
    echo "🗑️ Removing existing latest tag and re-tagging..."
    docker tag $IMAGE_NAME:$NEW_TAG $IMAGE_NAME:latest
    docker rmi $IMAGE_NAME:latest
else
    echo "✅ No existing latest image, tagging new one..."
    docker tag $IMAGE_NAME:$NEW_TAG $IMAGE_NAME:latest
fi

echo "✅ Tagged $IMAGE_NAME:$NEW_TAG as latest"

# values-local.yaml 파일에서 tag 값을 latest로 업데이트
if [[ -f "$VALUES_FILE" ]]; then
    sed -i.bak "s/tag: .*/tag: latest/" "$VALUES_FILE"
    echo "✅ Updated $VALUES_FILE with tag: latest"
else
    echo "⚠️ Error: $VALUES_FILE not found!"
    exit 1
fi

# 기존의 모든 날짜 태그 제거 (latest 제외)
echo "🗑️ Cleaning up old images (keeping only latest)..."

# 1️⃣ 현재 `latest` 태그가 가리키는 이미지 ID 저장
LATEST_IMAGE_ID=$(docker images -q $IMAGE_NAME:latest)

# 2️⃣ 날짜 형식(`YYYYMMDDHHMMSS`) 태그가 있는 이미지 목록 가져오기 (latest 제외)
OLD_TAGS=$(docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | grep "$IMAGE_NAME:" | grep -E '^[0-9]{14} ' | awk '{print $1}')

# 3️⃣ 기존 날짜 태그 삭제 (단, latest가 가리키는 이미지 ID는 제외)
if [[ -n "$OLD_TAGS" ]]; then
    for TAG in $OLD_TAGS; do
        TAG_IMAGE_ID=$(docker images -q $TAG)
        if [[ "$TAG_IMAGE_ID" != "$LATEST_IMAGE_ID" ]]; then
            echo "🗑️ Removing old tag: $TAG"
            docker rmi -f $TAG
        else
            echo "⚠️ Skipping deletion of $TAG as it is still referenced by latest"
        fi
    done
else
    echo "✅ No old images to remove."
fi

# 4️⃣ 사용되지 않는 dangling 이미지 삭제
echo "🗑️ Removing unused images..."
docker image prune -f

# 빌드 완료 후 최신 Docker 이미지 목록 확인
echo "🔍 Docker Images for $IMAGE_NAME:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep $IMAGE_NAME