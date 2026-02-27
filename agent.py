import requests
import os
from bs4 import BeautifulSoup
from loguru import logger
from typing import List
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
from openai_module import generate_headlines
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, HttpUrl
import uvicorn
from logtail import LogtailHandler
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger.add("agent.log", rotation="10 MB", level="INFO")

# Настройка BetterStack (Logtail)
betterstack_token = os.getenv("BETTERSTACK_TOKEN")
if betterstack_token:
    handler = LogtailHandler(source_token=betterstack_token)
    logger.add(handler, level="INFO")
    logger.info("BetterStack logging configured successfully")
else:
    logger.warning("BETTERSTACK_TOKEN not found in .env, remote logging disabled")

app = FastAPI(
    title="SEO Headlines Generator API",
    description="API для генерации SEO-заголовков на основе содержимого статьи по URL",
    version="1.0.0"
)

class HeadlineRequest(BaseModel):
    url: HttpUrl

class HeadlineResponse(BaseModel):
    status: int
    headlines: List[str] = []
    message: str = "Success"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_article_text(url: str) -> str:
    """
    Загружает HTML по ссылке и извлекает текст с помощью BeautifulSoup.
    
    Args:
        url (str): Ссылка на статью.
        
    Returns:
        str: Текст статьи.
    """
    logger.info(f"Загрузка статьи по URL: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        
        # Очищаем текст от лишних пробелов и переносов строк
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info("Текст статьи успешно извлечен.")
        return text
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при загрузке URL {url}: {e}")
        raise

def generate_seo_headlines(url: str) -> List[str]:
    """
    Генерирует 5 SEO-заголовков для статьи по указанному URL.
    
    Args:
        url (str): Ссылка на статью.
        
    Returns:
        List[str]: Список из 5 заголовков.
    """
    try:
        article_text = fetch_article_text(url)
        if not article_text:
            logger.warning("Не удалось извлечь текст из статьи.")
            raise ValueError("Empty article text")
            
        headlines = generate_headlines(article_text)
        
        if not headlines:
            logger.warning("Не удалось сгенерировать заголовки.")
            raise ValueError("Failed to generate headlines")
            
        logger.info(f"Сгенерировано {len(headlines)} заголовков.")
        return headlines
        
    except RetryError as e:
        logger.error(f"Не удалось загрузить статью после нескольких попыток: {e}")
        raise
    except Exception as e:
        logger.exception(f"Произошла ошибка в процессе генерации заголовков: {e}")
        raise

@app.post("/generate-headlines", response_model=HeadlineResponse)
async def create_headlines(request: HeadlineRequest):
    """
    Эндпоинт для генерации заголовков.
    Принимает JSON с полем 'url'.
    Возвращает JSON со статусом и списком заголовков.
    """
    try:
        url_str = str(request.url)
        headlines = generate_seo_headlines(url_str)
        return HeadlineResponse(
            status=200,
            headlines=headlines,
            message="Headlines generated successfully"
        )
    except RetryError:
        return HeadlineResponse(
            status=500,
            headlines=[],
            message="Failed to fetch article after multiple attempts"
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return HeadlineResponse(
            status=500,
            headlines=[],
            message=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    logger.info("Starting API server...")
    # Используем reload=True для удобства разработки, но в продакшене лучше без него
    uvicorn.run(app, host="0.0.0.0", port=8000)
