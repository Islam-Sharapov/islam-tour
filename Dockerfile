FROM python:3.11-slim

WORKDIR /app

# Копируем сервер и фронт
COPY server.py ./server.py
COPY public ./public

# По желанию: выставим дефолтные переменные (можно переопределять при запуске)
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]