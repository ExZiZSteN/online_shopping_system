FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Добавляем корень backend в PYTHONPATH, чтобы сервисы видели друг друга и общие модули
ENV PYTHONPATH=/app

WORKDIR /app

# Копируем зависимости из backend/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое backend/ в рабочий каталог контейнера
COPY . .

EXPOSE 8000