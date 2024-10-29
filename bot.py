import requests  # Для работы с API
import time  # Для паузы между запросами
import logging  # Для записи логов о действиях и ошибках
from telegram import Bot  # Для работы с Telegram-ботом
from datetime import datetime, timedelta  # Для работы с временем
from deep_translator import GoogleTranslator  # Библиотека для перевода

# Настройки
BOT_TOKEN = '7678223152:AAEi1VA2s0XPVF8yVrnAXxpd4sya4cLAZgA'  # Токен бота Telegram
CHANNEL_ID = '-1002325539147'  # ID канала для публикации новостей
API_KEY = 'fe7c40b8ed162413752d2b98fe4bac479ad1c6a56c62a5b93d113e9f3d31698b'  # Ключ API CryptoCompare
CRYPTO_API_URL = f'https://min-api.cryptocompare.com/data/v2/news/?lang=EN&api_key={API_KEY}'  # URL API для новостей

# Инициализация бота и логирования
bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
last_published_time = datetime.utcnow() - timedelta(minutes=5)  # Начальная точка времени

# Глобальный список для накопления новостей
pending_news = []

def fetch_news():
    """Получение новостей с CryptoCompare."""
    try:
        response = requests.get(CRYPTO_API_URL)  # Запрос к API
        response.raise_for_status()  # Проверка на ошибки
        news_data = response.json().get('Data', [])  # Получение списка новостей
        return news_data
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении новостей: {e}")
        return []

def filter_new_news(news_list):
    """Фильтрация только новых новостей."""
    global last_published_time
    new_news = []
    for article in news_list:
        published_time = datetime.utcfromtimestamp(article['published_on'])  # Время публикации новости
        if published_time > last_published_time:  # Проверка, новее ли новость
            new_news.append(article)
            last_published_time = max(last_published_time, published_time)  # Обновление времени последней новости
    return new_news

def translate_text(text):
    """Перевод текста на русский язык."""
    try:
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        logging.error(f"Ошибка при переводе: {e}")
        return text  # Если перевод не удался, возвращается оригинал

def determine_icon(title_ru):
    """Определение иконки на основе заголовка."""
    title_lower = title_ru.lower()
    if any(keyword in title_lower for keyword in ['meta', 'facebook', 'инстаграм', 'whatsapp']):
        return 'Ⓜ️'
    elif any(keyword in title_lower for keyword in ['биткоин', 'ethereum', 'криптовалюта', 'bitcoin', 'эфириум']):
        return '🪙'
    elif any(keyword in title_lower for keyword in ['взлом', 'хакер', 'безопасность', 'defi']):
        return '🚨'
    else:
        return '📰'

def send_single_news(news):
    """Отправка одной новости в Telegram-канал."""
    title = news['title']  # Заголовок
    # Перевод заголовка на русский язык
    title_ru = translate_text(title)
    # Определение иконки
    icon = determine_icon(title_ru)
    # Формирование строки новости
    message = f"{icon} {title_ru.strip()}\n\n@Inchainlive"

    try:
        bot.send_message(chat_id=CHANNEL_ID, text=message)
        logging.info("Новость успешно отправлена!")
        time.sleep(5)  # Пауза, чтобы избежать ограничения Telegram
    except Exception as e:
        logging.error(f"Ошибка при отправке новости: {e}")
        time.sleep(10)  # Дополнительная пауза при ошибке

def main():
    """Основная функция: периодически проверяет наличие новых новостей и отправляет их по одной."""
    global pending_news
    while True:
        logging.info("Проверка наличия новых новостей...")
        news_list = fetch_news()
        new_news = filter_new_news(news_list)
        if new_news:
            pending_news.extend(new_news)
            logging.info(f"Добавлено {len(new_news)} новых новостей. Всего ожидает: {len(pending_news)}")
            # Отправляем каждую новость по одной
            while pending_news:
                single_news = pending_news.pop(0)
                send_single_news(single_news)
        else:
            logging.info("Новых новостей нет.")
        time.sleep(5)  # Проверка каждые 2 минуты

if __name__ == '__main__':
    main()
