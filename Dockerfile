FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema necesarias para algunas wheels
RUN apt-get update && apt-get install -y build-essential gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

COPY . /app

# No ejecutar la app como root
RUN useradd --create-home appuser || true
USER appuser

EXPOSE 8000

# Gunicorn escucha en :8000 (Render/Azure/Cloud Run pueden mapear PUERTO)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app", "--workers", "2", "--threads", "4"]
