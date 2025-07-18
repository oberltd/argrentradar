# 🏠 ArgRentRadar - Argentina Real Estate Parser

**ArgRentRadar** - это комплексное решение для автоматического сбора, обработки и предоставления данных о недвижимости из популярных аргентинских сайтов объявлений.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-argrentradar-black.svg)](https://github.com/oberltd/argrentradar)

## 🏠 Описание

Этот проект представляет собой комплексное решение для сбора, обработки и предоставления данных о недвижимости из популярных аргентинских сайтов объявлений. Система включает в себя веб-скрапинг, API для доступа к данным и веб-интерфейс для управления.

### Поддерживаемые сайты:
- **ZonaProp.com.ar** - ведущий портал недвижимости в Аргентине
- **ArgenProp.com** - популярная платформа поиска недвижимости
- **MercadoLibre.com.ar** - крупнейшая торговая площадка ✅
- **RE/MAX Argentina** - международная сеть недвижимости ✅
- **Properati.com.ar** - современная платформа недвижимости ✅
- **Inmuebles24.com** - популярный портал объявлений ✅
- **Navent.com** - технологическая платформа недвижимости ✅

## 🚀 Возможности

### Основные функции:
- **Автоматический парсинг** объявлений с 7 популярных сайтов
- **RESTful API** для доступа к данным
- **Веб-дашборд** для мониторинга и управления
- **Фильтрация и поиск** по различным критериям
- **Отслеживание изменений** цен и статусов объявлений
- **Статистика и аналитика** по рынку недвижимости
- **Асинхронная обработка** для высокой производительности

### 🤖 AI-возможности (DeepSeek R1):
- **Интеллектуальный анализ** описаний недвижимости
- **Автоматическое улучшение** текстов объявлений
- **Извлечение ключевых характеристик** из неструктурированного текста
- **Генерация SEO-оптимизированных** заголовков и описаний
- **Анализ рынка** и генерация инсайтов
- **Перевод на английский** для международных клиентов
- **Генерация контента** для социальных сетей

## 📋 Требования

### Основные:
- Python 3.8+
- PostgreSQL или SQLite
- Redis (опционально, для кэширования)

### Для AI-функций:
- Ollama или Docker (для локальной LLM)
- 8GB+ RAM (рекомендуется 16GB)
- GPU с CUDA (опционально, для ускорения)

## 🛠 Установка

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd argentina_real_estate_parser
```

2. **Установка зависимостей:**
```bash
pip install -r requirements.txt
```

3. **Настройка окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

4. **Инициализация базы данных:**
```bash
python main.py init-db
```

## 🔧 Конфигурация

Основные настройки в файле `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/argentina_real_estate

# API
API_HOST=0.0.0.0
API_PORT=12000
API_DEBUG=True

# Scraping
SCRAPING_DELAY=1
MAX_CONCURRENT_REQUESTS=10
USER_AGENT_ROTATION=True

# LLM Configuration (опционально)
LLM_ENABLED=true
DEEPSEEK_BASE_URL=http://localhost:11434
DEEPSEEK_MODEL=deepseek-r1:latest
```

### 5. **Настройка DeepSeek R1 LLM (опционально):**

Для использования AI-функций установите и настройте DeepSeek R1:

```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama
ollama serve

# Загрузка модели DeepSeek R1
ollama pull deepseek-r1:latest
```

Подробная инструкция: [DEEPSEEK_SETUP.md](DEEPSEEK_SETUP.md)

## 🚀 Запуск

### Веб-сервер API:
```bash
python main.py api
```

### Ручной запуск парсинга:
```bash
python main.py scrape
```

### С отладкой:
```bash
python main.py api --debug
```

## 📖 API Документация

После запуска сервера API документация доступна по адресам:
- **Swagger UI**: http://localhost:12000/docs
- **ReDoc**: http://localhost:12000/redoc
- **Дашборд**: http://localhost:12000/

### Основные эндпоинты:

#### Недвижимость
- `GET /api/v1/properties` - Поиск объектов недвижимости
- `GET /api/v1/properties/{id}` - Получить объект по ID
- `GET /api/v1/properties/recent/new` - Новые объекты
- `GET /api/v1/properties/recent/updated` - Обновленные объекты

#### Парсинг
- `POST /api/v1/scraping/start` - Запустить парсинг
- `GET /api/v1/scraping/status` - Статус парсинга
- `GET /api/v1/scraping/sessions` - История сессий парсинга

#### Статистика
- `GET /api/v1/statistics/properties` - Статистика по недвижимости
- `GET /api/v1/statistics/scraping` - Статистика парсинга
- `GET /api/v1/statistics/overview` - Общая статистика

#### 🤖 LLM и AI
- `GET /api/v1/llm/health` - Статус LLM сервиса
- `POST /api/v1/llm/analyze/property` - Анализ недвижимости
- `POST /api/v1/llm/analyze/text` - Анализ текста
- `POST /api/v1/llm/enhance/description` - Улучшение описания
- `POST /api/v1/llm/generate/summary` - Генерация резюме
- `POST /api/v1/llm/translate/english` - Перевод на английский
- `POST /api/v1/llm/social/post` - Генерация поста для соцсетей
- `GET /api/v1/llm/market/insights` - Анализ рынка

## 🔍 Примеры использования

### Поиск квартир в Буэнос-Айресе:
```bash
curl "http://localhost:12000/api/v1/properties?property_type=apartment&city=Buenos%20Aires&min_price=100000&max_price=500000"
```

### Запуск парсинга с фильтрами:
```bash
curl -X POST "http://localhost:12000/api/v1/scraping/start" \
  -H "Content-Type: application/json" \
  -d '{
    "property_type": "apartment",
    "operation_type": "sale",
    "min_price": 100000,
    "max_price": 1000000,
    "city": "Buenos Aires"
  }'
```

### 🤖 Использование AI-функций:

#### Анализ описания недвижимости:
```bash
curl -X POST "http://localhost:12000/api/v1/llm/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Departamento 2 ambientes en Palermo, 45m², balcón, cocina integrada, muy luminoso"
  }'
```

#### Улучшение описания:
```bash
curl -X POST "http://localhost:12000/api/v1/llm/enhance/description" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Depto 2 amb Palermo",
    "description": "Lindo depto en Palermo con balcon",
    "features": {
      "location": "Palermo, Buenos Aires",
      "property_type": "departamento"
    }
  }'
```

#### Генерация поста для Instagram:
```bash
curl -X POST "http://localhost:12000/api/v1/llm/social/post?platform=instagram" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Departamento en Palermo",
    "location": "Palermo, Buenos Aires",
    "price": 250000,
    "features": ["2 dormitorios", "balcón", "luminoso"]
  }'
```

## 📊 Структура данных

### Объект недвижимости:
```json
{
  "id": 123,
  "external_id": "prop_456",
  "source_url": "https://zonaprop.com.ar/...",
  "source_website": "zonaprop.com.ar",
  "title": "Departamento 2 ambientes en Palermo",
  "description": "Hermoso departamento...",
  "property_type": "apartment",
  "operation_type": "sale",
  "location": {
    "country": "Argentina",
    "province": "Buenos Aires",
    "city": "Buenos Aires",
    "neighborhood": "Palermo",
    "address": "Av. Santa Fe 1234"
  },
  "features": {
    "bedrooms": 2,
    "bathrooms": 1,
    "total_area": 65.0,
    "parking_spaces": 1
  },
  "price": {
    "amount": 250000,
    "currency": "USD",
    "expenses": 15000,
    "expenses_currency": "ARS"
  },
  "contact": {
    "agency_name": "Inmobiliaria XYZ",
    "phone": "+54 11 1234-5678"
  },
  "images": {
    "main_image": "https://...",
    "gallery": ["https://...", "https://..."]
  }
}
```

## 🏗 Архитектура

```
src/
├── models/          # Pydantic модели данных
├── parsers/         # Парсеры для различных сайтов
├── database/        # SQLAlchemy модели и подключение к БД
├── services/        # Бизнес-логика
├── api/            # FastAPI роутеры и эндпоинты
├── utils/          # Утилиты и конфигурация
└── scrapers/       # Scrapy пауки (планируется)
```

## 🔄 Процесс парсинга

1. **Инициализация** - Создание сессии парсинга
2. **Получение списков** - Парсинг страниц с объявлениями
3. **Детальный парсинг** - Извлечение подробной информации
4. **Обработка данных** - Нормализация и валидация
5. **Сохранение** - Запись в базу данных
6. **Отслеживание изменений** - Сравнение с существующими данными

## 📈 Мониторинг

Система предоставляет различные метрики:
- Количество обработанных объектов
- Скорость парсинга
- Ошибки и их типы
- Статистика по источникам
- Изменения цен

## 🛡 Ограничения и этика

- Соблюдение robots.txt
- Разумные задержки между запросами
- Ротация User-Agent
- Уважение к серверам сайтов-источников

## 🔮 Планы развития

- [ ] Добавление новых сайтов-источников
- [ ] Система уведомлений о новых объектах
- [ ] Машинное обучение для оценки недвижимости
- [ ] Мобильное приложение
- [ ] Интеграция с картами
- [ ] Экспорт данных в различные форматы

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста:

1. Создайте форк репозитория
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.

## 📞 Поддержка

Если у вас есть вопросы или проблемы:
- Создайте Issue в GitHub: https://github.com/oberltd/argrentradar/issues
- Проверьте документацию в репозитории

## 🔗 Ссылки

- **GitHub Repository**: https://github.com/oberltd/argrentradar
- **API Documentation**: http://localhost:12000/docs (после запуска)
- **Web Dashboard**: http://localhost:12000/ (после запуска)

## 🙏 Благодарности

- Команде FastAPI за отличный фреймворк
- Разработчикам BeautifulSoup и Scrapy
- Сообществу Python за инструменты и библиотеки

---

**ArgRentRadar** - Ваш радар аргентинской недвижимости! 🏠🇦🇷