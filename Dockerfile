FROM python:3.14-slim

# file prep
WORKDIR /app
COPY progkeeper progkeeper
COPY schema.sql .
COPY requirements.txt .

# prep APT
RUN apt-get update -y

# install Mariadb dependencies
# needed for pip to not error
RUN apt-get install -y libmariadb-dev build-essential

# install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "progkeeper.api:app", "--host", "0.0.0.0", "--port", "8000"]