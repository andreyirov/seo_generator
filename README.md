# Генератор SEO-заголовков (API)

Сервис на FastAPI, который на основе статьи по URL генерирует 5 цепляющих SEO-заголовков, используя OpenAI API.

## Функциональность

- **API**: REST API с эндпоинтом для генерации заголовков.
- **Загрузка**: Извлекает основной текст статьи по URL.
- **Генерация**: Создает 5 вариантов SEO-заголовков с помощью LLM.
- **Логирование**: Поддержка BetterStack (Logtail) и локального логирования.
- **Надежность**: Автоматические повторные попытки при сбоях.

## Требования

- Python >= 3.10
- Docker (опционально)

## Установка и запуск (Локально)

1. Клонируйте репозиторий.
2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Создайте файл `.env` в корне проекта:
   ```env
   PROXYAPIKEY=ваш_ключ_api
   MODEL=openai/gpt-4o
   OPENAPIURL=https://openai.api.proxyapi.ru/v1
   BETTERSTACK_TOKEN=ваш_токен_betterstack (опционально)
   ```
4. Запустите сервер:
   ```bash
   uvicorn agent:app --host 0.0.0.0 --port 8000 --reload
   ```

## Установка и запуск (Docker)

1. Соберите образ:
   ```bash
   docker build -t seo-generator .
   ```
2. Запустите контейнер (передав файл .env):
   ```bash
   docker run -d -p 8000:8000 --env-file .env --name seo-app seo-generator
   ```

## Использование API

**Эндпоинт:** `POST /generate-headlines`

**Запрос:**
```json
{
  "url": "https://habr.com/ru/articles/788382/"
}
```

**Пример cURL:**
```bash
curl -X POST "http://localhost:8000/generate-headlines" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://habr.com/ru/articles/788382/"}'
```

**Ответ:**
```json
{
  "status": 200,
  "headlines": [
    "Заголовок 1",
    "Заголовок 2",
    ...
  ],
  "message": "Headlines generated successfully"
}
```
