FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python generate_logs.py && python build_db.py

EXPOSE 3001

CMD ["python", "app.py"]
