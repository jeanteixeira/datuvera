FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the python package, alembic config, and tests to avoid creating
# a top-level `main.py` that conflicts with the package `app`.
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic
COPY ./tests ./tests

CMD ["/bin/sh", "-c", "alembic upgrade head || true && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
