FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shl_scraper.py .
COPY recommendation_engine.py .
COPY fastapi_backend.py .
COPY shl_assessments.json .

EXPOSE 8000

CMD ["uvicorn", "fastapi_backend:app", "--host", "0.0.0.0", "--port", "8000"]