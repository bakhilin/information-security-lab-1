FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data && chmod 755 /app/data

WORKDIR /app/

# RUN python init_db.py

# RUN useradd -m -u 1000 user && chown -R user:user /app
# USER user

EXPOSE 5000

CMD ["python", "app.py"]