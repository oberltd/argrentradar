# 🤖 DeepSeek R1 LLM Integration Setup

Эта документация описывает, как настроить и интегрировать локальную LLM DeepSeek R1 с ArgRentRadar.

## 📋 Требования

- Docker или Ollama для запуска локальной LLM
- Минимум 8GB RAM (рекомендуется 16GB+)
- GPU с поддержкой CUDA (опционально, для ускорения)

## 🚀 Установка DeepSeek R1

### Вариант 1: Использование Ollama (Рекомендуется)

1. **Установка Ollama:**
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Скачайте установщик с https://ollama.ai/download
```

2. **Запуск Ollama:**
```bash
ollama serve
```

3. **Загрузка модели DeepSeek R1:**
```bash
# Загрузка базовой модели
ollama pull deepseek-r1:latest

# Или более легкая версия для слабых машин
ollama pull deepseek-r1:7b
```

4. **Проверка установки:**
```bash
ollama list
curl http://localhost:11434/api/tags
```

### Вариант 2: Использование Docker

1. **Создание Dockerfile для DeepSeek:**
```dockerfile
FROM ollama/ollama:latest

# Копируем модель (если есть локально)
# COPY deepseek-r1.gguf /models/

# Устанавливаем модель
RUN ollama pull deepseek-r1:latest

EXPOSE 11434

CMD ["ollama", "serve"]
```

2. **Сборка и запуск:**
```bash
docker build -t deepseek-r1 .
docker run -d -p 11434:11434 --name deepseek deepseek-r1
```

### Вариант 3: Использование OpenAI-совместимого API

Если у вас есть доступ к DeepSeek API или другому совместимому сервису:

```bash
# Установите переменные окружения
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
export DEEPSEEK_API_KEY="your-api-key-here"
```

## ⚙️ Конфигурация ArgRentRadar

### 1. Переменные окружения

Создайте или обновите файл `.env`:

```env
# LLM Configuration
LLM_ENABLED=true
DEEPSEEK_BASE_URL=http://localhost:11434
DEEPSEEK_MODEL=deepseek-r1:latest
DEEPSEEK_TIMEOUT=30
DEEPSEEK_API_KEY=  # Оставьте пустым для локального Ollama
```

### 2. Проверка конфигурации

```bash
# Запустите ArgRentRadar
python main.py api

# Проверьте статус LLM
curl http://localhost:12000/api/v1/llm/health
```

## 🧪 Тестирование интеграции

### 1. Проверка здоровья LLM

```bash
curl -X GET "http://localhost:12000/api/v1/llm/health"
```

Ожидаемый ответ:
```json
{
  "status": "healthy",
  "model": "deepseek-r1:latest",
  "base_url": "http://localhost:11434",
  "enabled": true
}
```

### 2. Анализ текста

```bash
curl -X POST "http://localhost:12000/api/v1/llm/analyze/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Departamento 2 ambientes en Palermo, 45m², balcón, cocina integrada, muy luminoso"
  }'
```

### 3. Улучшение описания

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

## 🔧 Настройка производительности

### Для слабых машин:

```env
# Используйте более легкую модель
DEEPSEEK_MODEL=deepseek-r1:7b

# Увеличьте таймаут
DEEPSEEK_TIMEOUT=60
```

### Для мощных машин с GPU:

```bash
# Установите CUDA поддержку для Ollama
ollama pull deepseek-r1:latest --gpu

# Или используйте более мощную модель
ollama pull deepseek-r1:32b
```

## 📊 Мониторинг и логи

### Проверка логов Ollama:
```bash
# Логи Ollama
journalctl -u ollama -f

# Или для Docker
docker logs deepseek -f
```

### Проверка логов ArgRentRadar:
```bash
tail -f logs/app.log | grep -i llm
```

## 🚨 Устранение неполадок

### Проблема: LLM недоступна

**Решение:**
1. Проверьте, что Ollama запущена: `curl http://localhost:11434/api/tags`
2. Проверьте, что модель загружена: `ollama list`
3. Проверьте настройки в `.env`

### Проблема: Медленные ответы

**Решение:**
1. Используйте более легкую модель
2. Увеличьте `DEEPSEEK_TIMEOUT`
3. Проверьте загрузку системы

### Проблема: Ошибки памяти

**Решение:**
1. Используйте модель меньшего размера
2. Закройте другие приложения
3. Увеличьте swap-файл

## 🔄 Обновление модели

```bash
# Обновление до новой версии
ollama pull deepseek-r1:latest

# Перезапуск ArgRentRadar
python main.py api
```

## 📈 Оптимизация для продакшена

### 1. Использование GPU

```bash
# Проверка поддержки GPU
nvidia-smi

# Запуск с GPU
ollama serve --gpu
```

### 2. Кэширование

```env
# Включите кэширование в Redis
REDIS_URL=redis://localhost:6379/1
```

### 3. Балансировка нагрузки

Для высоких нагрузок рассмотрите запуск нескольких экземпляров:

```bash
# Запуск нескольких экземпляров Ollama
ollama serve --port 11434 &
ollama serve --port 11435 &
ollama serve --port 11436 &
```

## 🔐 Безопасность

### 1. Ограничение доступа

```bash
# Ограничьте доступ к Ollama только с localhost
ollama serve --host 127.0.0.1
```

### 2. Мониторинг использования

```bash
# Мониторинг ресурсов
htop
nvidia-smi -l 1
```

## 📚 Дополнительные ресурсы

- [Ollama Documentation](https://ollama.ai/docs)
- [DeepSeek Model Documentation](https://github.com/deepseek-ai/DeepSeek-R1)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

## 🆘 Поддержка

Если у вас возникли проблемы с настройкой LLM:

1. Проверьте логи: `tail -f logs/app.log`
2. Проверьте статус: `curl http://localhost:12000/api/v1/llm/health`
3. Создайте issue в GitHub: https://github.com/oberltd/argrentradar/issues

---

**Примечание:** DeepSeek R1 - это мощная модель, которая значительно улучшает качество анализа и обработки данных о недвижимости. Правильная настройка обеспечит оптимальную производительность системы.