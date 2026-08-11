FROM python:3.12-slim

WORKDIR /app

COPY src ./src

ENV PYTHONPATH=/app/src

CMD ["python", "-c", "from server_example.main import main; main()"]
