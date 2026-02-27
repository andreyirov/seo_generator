#!/bin/bash

# Переменные окружения для контейнера
export PROXYAPIKEY="sk-qmbNx6FDUJsPZcB3PPBcq0DqBpkYuecy"
export MODEL="openai/gpt-4o"
export OPENAPIURL="https://openai.api.proxyapi.ru/v1"
export BETTERSTACK_TOKEN="your_token_here"

# Настройки
REPO_URL="https://github.com/andreyirov/seo_generator.git"
REPO_DIR="/app/seo_generator" # Путь, куда будет клонироваться репо
CONTAINER_NAME="seo-app"
IMAGE_NAME="seo-generator"
BRANCH_NAME="api_server"

# Функция для запуска контейнера
start_container() {
    echo "Запускаем контейнер $CONTAINER_NAME..."
    docker run -d -p 8000:8000 \
      -e PROXYAPIKEY="$PROXYAPIKEY" \
      -e MODEL="$MODEL" \
      -e OPENAPIURL="$OPENAPIURL" \
      -e BETTERSTACK_TOKEN="$BETTERSTACK_TOKEN" \
      --name "$CONTAINER_NAME" \
      "$IMAGE_NAME"
}

# Функция для пересборки и перезапуска
rebuild_and_restart() {
    echo "Изменения обнаружены. Пересборка..."
    
    # Остановка и удаление старого контейнера
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        echo "Останавливаем старый контейнер..."
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi

    # Сборка нового образа
    echo "Сборка образа $IMAGE_NAME..."
    docker build -t "$IMAGE_NAME" .

    # Запуск
    start_container
}

# Проверка наличия директории репозитория
if [ ! -d "$REPO_DIR" ]; then
    echo "Репозиторий не найден. Клонируем..."
    git clone -b "$BRANCH_NAME" "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR" || exit 1
    
    # Первичная сборка и запуск
    rebuild_and_restart
    exit 0
fi

cd "$REPO_DIR" || exit 1

# Убедимся, что мы на нужной ветке
git checkout "$BRANCH_NAME"

# Получаем хэш текущего коммита
LOCAL_HASH=$(git rev-parse HEAD)

# Обновляем информацию о ветках
git fetch origin

# Получаем хэш удаленного коммита
REMOTE_HASH=$(git rev-parse "origin/$BRANCH_NAME")

# Проверяем, запущен ли контейнер
CONTAINER_RUNNING=$(docker ps -q -f name=$CONTAINER_NAME)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ] || [ -z "$CONTAINER_RUNNING" ]; then
    if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
        echo "Обнаружены изменения в репозитории."
        echo "Локальный: $LOCAL_HASH"
        echo "Удаленный: $REMOTE_HASH"
        
        # Обновляем код
        git pull origin "$BRANCH_NAME"
    else
        echo "Контейнер не запущен, но код актуален."
    fi
    
    rebuild_and_restart
else
    echo "Изменений нет. Контейнер работает."
fi
