FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./main.py
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

EXPOSE 9108
CMD ["./start.sh"]
