import requests
import sys
from bs4 import BeautifulSoup
from loguru import logger
from typing import List
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
from openai_module import generate_headlines

# Настройка логирования
logger.add("agent.log", rotation="10 MB", level="INFO")

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
            return []
            
        headlines = generate_headlines(article_text)
        
        if not headlines:
            logger.warning("Не удалось сгенерировать заголовки.")
            return []
            
        logger.info(f"Сгенерировано {len(headlines)} заголовков.")
        return headlines
        
    except RetryError as e:
        logger.error(f"Не удалось загрузить статью после нескольких попыток: {e}")
        return []
    except Exception as e:
        logger.exception(f"Произошла ошибка в процессе генерации заголовков: {e}")
        return []

if __name__ == "__main__":
    # Получаем URL из аргументов командной строки или используем дефолтный
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        # Добавляем схему, если её нет
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
    else:
        target_url = "https://habr.com/ru/articles/788382/" # Пример статьи с Хабра
        print("URL не передан, используется тестовый URL.")

    print(f"Генерация заголовков для: {target_url}")
    headlines = generate_seo_headlines(target_url)
    
    if headlines:
        print("\nСгенерированные SEO-заголовки:")
        for idx, headline in enumerate(headlines, 1):
            print(f"{idx}. {headline}")
    else:
        print("\nНе удалось сгенерировать заголовки.")
