import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем настройки из переменных окружения
API_KEY = os.getenv("PROXYAPIKEY")
BASE_URL = os.getenv("OPENAPIURL")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

if not API_KEY:
    logger.error("Переменная окружения PROXYAPIKEY не найдена.")
    raise ValueError("PROXYAPIKEY environment variable is not set")

if not BASE_URL:
    logger.error("Переменная окружения OPENAPIURL не найдена.")
    raise ValueError("OPENAPIURL environment variable is not set")

# Инициализируем клиент OpenAI
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def generate_headlines(article_text: str) -> List[str]:
    """
    Генерирует 5 SEO-заголовков на основе текста статьи.
    
    Args:
        article_text (str): Текст статьи.
        
    Returns:
        List[str]: Список из 5 заголовков.
    """
    logger.info("Отправка запроса к LLM для генерации заголовков.")
    
    system_prompt = "Ты опытный профессиональный SEO-редактор. Придумай 5 заголовков."
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": article_text}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        if not content:
            logger.warning("Получен пустой ответ от модели.")
            return []

        # Обработка ответа: предполагаем, что модель вернет список, разделенный переносами строк
        # или нумерованный список. Попробуем очистить и разбить на строки.
        headlines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Убираем нумерацию (например, "1. Заголовок") если она есть
        cleaned_headlines = []
        for line in headlines:
            # Удаляем цифры и точки в начале строки, если они есть
            clean_line = line.lstrip("0123456789.- ")
            # Удаляем markdown-жирность и кавычки
            clean_line = clean_line.strip('*').strip('"').strip()
            if clean_line:
                cleaned_headlines.append(clean_line)
        
        # Ограничиваем список 5 заголовками, если их больше
        return cleaned_headlines[:5]

    except Exception as e:
        logger.error(f"Ошибка при обращении к API OpenAI: {e}")
        raise
