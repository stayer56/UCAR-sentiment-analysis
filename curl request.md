## Примеры API-запросов

### 1. Добавление отзыва

**Запрос:**
curl -X 'POST' \
  'http://localhost:8000/reviews' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Отлично"
}'

**Ответ:**
{
  "id": 3,
  "text": "Отлично",
  "sentiment": "positive",
  "created_at": "2025-07-30T09:45:13.179905"
}

### 2. Получение отзывов с фильтрацией

**Запрос (все отзывы):**
curl -X 'GET' \
  'http://localhost:8000/reviews' \
  -H 'accept: application/json'

**Ответ:**
[
  {
    "id": 1,
    "text": "Нормальный сервис, но можно лучше",
    "sentiment": "neutral",
    "created_at": "2025-07-30T09:40:33.852346"
  },
  {
    "id": 2,
    "text": "Нормальный сервис, но можно лучше",
    "sentiment": "neutral",
    "created_at": "2025-07-30T09:44:11.962053"
  },
  {
    "id": 3,
    "text": "Отлично",
    "sentiment": "positive",
    "created_at": "2025-07-30T09:45:13.179905"
  }
]
