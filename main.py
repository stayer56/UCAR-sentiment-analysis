# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel  # Для валидации данных запросов/ответов
import sqlite3  # Работа с SQLite базой данных
from datetime import datetime  # Для работы с датами
from typing import Optional  # Для аннотации типов

# Инициализация FastAPI приложения
app = FastAPI(
    title="Sentiment Analysis API",
    description="Сервис для анализа тональности отзывов",
    version="1.0.0"
)

# ==============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ==============================================

def init_db():
    """Функция инициализации базы данных.
    Создает таблицу reviews, если она не существует.
    """
    try:
        # Подключаемся к базе данных (файл reviews.db будет создан автоматически)
        conn = sqlite3.connect('reviews.db')
        cursor = conn.cursor()
        
        # SQL-запрос для создания таблицы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  # Автоинкрементируемый ID
                text TEXT NOT NULL,                    # Текст отзыва
                sentiment TEXT NOT NULL,              # Тонональность (positive/neutral/negative)
                created_at TEXT NOT NULL              # Дата создания в ISO формате
            )
        ''')
        conn.commit()  # Применяем изменения
    except Exception as e:
        # В реальном проекте здесь должна быть обработка ошибок
        print(f"Ошибка при инициализации БД: {e}")
    finally:
        if conn:
            conn.close()  # Всегда закрываем соединение

# Вызываем инициализацию при старте приложения
init_db()

# ==============================================
# МОДЕЛИ PYDANTIC
# ==============================================

class ReviewRequest(BaseModel):
    """Модель для входящего запроса на добавление отзыва"""
    text: str  # Обязательное поле с текстом отзыва

class ReviewResponse(BaseModel):
    """Модель для ответа с данными отзыва"""
    id: int           # ID в базе данных
    text: str         # Текст отзыва
    sentiment: str    # Определенная тональность
    created_at: str   # Дата создания в ISO формате

# ==============================================
# АНАЛИЗ ТОНАЛЬНОСТИ
# ==============================================

def analyze_sentiment(text: str) -> str:
    """Функция определения тональности текста по ключевым словам.
    
    Args:
        text: Входной текст для анализа
        
    Returns:
        'positive', 'negative' или 'neutral'
    """
    text = text.lower()  # Приводим к нижнему регистру для унификации
    
    # Списки ключевых слов для разных тональностей
    positive_words = ['хорош', 'отличн', 'прекрасн', 'люблю', 'нравится', 'супер', 'класс']
    negative_words = ['плох', 'ужасн', 'ненавиж', 'отвратительн', 'кошмар', 'разочарован']
    
    # Проверяем наличие положительных слов
    if any(word in text for word in positive_words):
        return 'positive'
    
    # Проверяем наличие отрицательных слов
    elif any(word in text for word in negative_words):
        return 'negative'
    
    # Если ничего не найдено - нейтральный
    return 'neutral'

# ==============================================
# API ЭНДПОИНТЫ
# ==============================================

@app.post("/reviews", response_model=ReviewResponse)
async def create_review(review: ReviewRequest):
    """Эндпоинт для добавления нового отзыва.
    
    1. Анализирует тональность текста
    2. Сохраняет в базу данных
    3. Возвращает созданный отзыв с ID
    
    Args:
        review: Объект с текстом отзыва (ReviewRequest)
        
    Returns:
        ReviewResponse: Созданный отзыв с данными из БД
    """
    # Определяем тональность
    sentiment = analyze_sentiment(review.text)
    
    # Получаем текущую дату и время в ISO формате
    created_at = datetime.utcnow().isoformat()
    
    try:
        # Подключаемся к БД
        conn = sqlite3.connect('reviews.db')
        cursor = conn.cursor()
        
        # Вставляем новый отзыв
        cursor.execute(
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
            (review.text, sentiment, created_at)
        )
        
        # Получаем ID созданной записи
        review_id = cursor.lastrowid
        
        # Применяем изменения
        conn.commit()
        
        # Формируем ответ
        return {
            "id": review_id,
            "text": review.text,
            "sentiment": sentiment,
            "created_at": created_at
        }
        
    except Exception as e:
        # В реальном проекте нужно логировать ошибку
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при сохранении отзыва: {str(e)}"
        )
    finally:
        if conn:
            conn.close()  # Закрываем соединение в любом случае

@app.get("/reviews", response_model=list[ReviewResponse])
async def get_reviews(sentiment: Optional[str] = None):
    """Эндпоинт для получения списка отзывов.
    
    Поддерживает фильтрацию по тональности через параметр ?sentiment=
    
    Args:
        sentiment: Опциональный фильтр (positive/negative/neutral)
        
    Returns:
        Список отзывов в формате ReviewResponse
    """
    try:
        conn = sqlite3.connect('reviews.db')
        cursor = conn.cursor()
        
        # Формируем SQL-запрос в зависимости от наличия фильтра
        if sentiment:
            # Проверяем, что передан корректный фильтр
            if sentiment not in ['positive', 'negative', 'neutral']:
                raise HTTPException(
                    status_code=400,
                    detail="Недопустимое значение sentiment. Допустимо: positive, negative, neutral"
                )
                
            cursor.execute(
                "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?",
                (sentiment,)
            )
        else:
            # Без фильтра - выбираем все записи
            cursor.execute("SELECT id, text, sentiment, created_at FROM reviews")
        
        # Преобразуем результат в список словарей
        reviews = [
            {
                "id": row[0],
                "text": row[1],
                "sentiment": row[2],
                "created_at": row[3]
            }
            for row in cursor.fetchall()  # Получаем все строки
        ]
        
        return reviews
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении отзывов: {str(e)}"
        )
    finally:
        if conn:
            conn.close()

# ==============================================
# ЗАПУСК СЕРВЕРА ДЛЯ РАЗРАБОТКИ
# ==============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)