# Beauty Pinterest Bot

AI-система для автоматического продвижения Telegram-канала через Pinterest в нише Beauty.

## Функционал

- **Создание контента** — AI-генерация заголовков, описаний, SEO-ключевых слов и хэштегов
- **Генерация изображений** — создание Pinterest-пинов через OpenAI DALL-E 3 / Flux
- **Автопостинг** — автоматическая публикация пинов по расписанию
- **Мировые тренды** — анализ трендов из 5 регионов (США, Европа, Япония, Корея, Китай)
- **Beauty тренды** — поиск контентных возможностей в beauty-категориях
- **Аналитика** — статистика пинов, графики, CTR, рекомендации AI
- **Библиотека референсов** — сохранение и анализ референсного контента
- **Самообучение** — оптимизация стратегии на основе собранных данных

## Технологии

- Python 3.11+
- aiogram 3.x
- PostgreSQL + SQLAlchemy (async)
- Redis
- APScheduler
- OpenAI API (GPT-4o, DALL-E 3)
- Pinterest API v5
- Docker / Docker Compose

## Установка

1. Клонируйте репозиторий:
`git clone <repo-url>`
`cd beauty-pinterest-bot`

2. Настройте переменные окружения в файле `.env`:
```
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
PINTEREST_TOKEN=your_pinterest_token
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/beauty_bot
OWNER_ID=your_telegram_id
```

3. Запустите через Docker Compose:
`docker-compose up -d --build`

## Структура проекта

```
app/
├── bot/
│   ├── handlers/      # Обработчики команд Telegram
│   └── services/      # Pinterest API, перевод
├── ai/                # AI модули (генерация, анализ трендов)
├── analytics/         # Сбор статистики, графики, оптимизация
├── database/          # Модели БД, репозитории
├── images/            # Обработка изображений
├── scheduler/         # Планировщик задач
└── utils/             # Конфигурация, логирование
```

## Разработка на BotHost

Проект готов к деплою на BotHost. Убедитесь, что в `.env` указаны все необходимые переменные, и загрузите проект через Git.
