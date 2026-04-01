# Ads Moderation Service

Сервис модерации объявлений на FastAPI с ML-моделью, PostgreSQL и асинхронной обработкой через Kafka/Redpanda.

## Что умеет сервис

- синхронное предсказание через `/predict`
- упрощённое предсказание по `item_id` через `/simple_predict`
- асинхронная модерация через Kafka:
  - `POST /async_predict`
  - `GET /moderation_result/{task_id}`
- сохранение результатов модерации в PostgreSQL
- обработка ошибок через Dead Letter Queue (`moderation_dlq`)
- запуск отдельного воркера для обработки очереди

---

## Структура проекта

```text
.
├── main.py
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── migrations/
│   ├── 001_init.up.sql
│   ├── 002_moderation_results.up.sql
│   └── 003_add_is_closed.up.sql
├── app/
│   ├── main.py
│   ├── db.py
│   ├── model.py
│   ├── schemas.py
│   ├── clients/
│   │   ├── kafka.py
│   │   └── redis.py
│   ├── repositories/
│   │   ├── users.py
│   │   ├── items.py
│   │   └── moderation_results.py
│   ├── routes/
│   │   ├── predict.py
│   │   ├── async_moderation.py
│   │   └── items.py
│   ├── services/
│   │   └── prediction.py
│   ├── storages/
│   │   └── prediction_cache.py
│   └── workers/
│       └── moderation_worker.py
└── tests/
    ├── test_predict.py
    ├── test_simple_predict.py
    ├── test_async_moderation.py
    ├── test_worker.py
    ├── test_predict_cache_unit.py
    ├── test_moderation_result_cache_unit.py
    ├── test_close_item_unit.py
    └── integration/
        ├── test_prediction_cache_integration.py
        └── test_postgres_repositories_integration.py

```

---

## Запуск проекта

Считаем, что бд настроена

### Установить зависимости Python
```bash
pip install -r requirements.txt
```

### Запустить инфраструктуру через Docker
```bash
docker compose up -d
```

### Проверить, что контейнеры поднялись:
```bash
docker compose ps
```

После запуска будут доступны:

PostgreSQL: localhost:5432
Redpanda (Kafka): localhost:9092
Redpanda Console: http://localhost:8080

### Запустить FastAPI-приложение

```bash
uvicorn main:app --reload
```

После запуска Swagger будет доступен по адресу: http://127.0.0.1:8000/docs

### Запустить Kafka-воркер
В отдельном терминале:

```bash
python -m app.workers.moderation_worker
```
