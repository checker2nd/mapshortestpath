# backend/Dockerfile
FROM python:3.10-slim

# OSレベルの依存ライブラリ（OSMnx, GDAL など）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gdal-bin libgdal-dev libspatialindex-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 依存関係を先にインストール（キャッシュ活用）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリコードをコピー
COPY . .

# FastAPI を uvicorn で起動
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
