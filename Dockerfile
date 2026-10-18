FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python3","-m","uvicorn","main:app","--host","0.0.0.0","--port","8080"]
