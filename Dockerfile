FROM python:3.14-slim

WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY progkeeper progkeeper

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "progkeeper.api:app", "--host", "0.0.0.0", "--port", "8000"]