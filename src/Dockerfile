# ERP - Tienda de Tecnologia
# Imagen base: Python 3.12 slim (ligera, solo lo necesario)
FROM python:3.12-slim

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar psycopg2
# libpq-dev: libreria cliente de PostgreSQL
# gcc: compilador C necesario para psycopg2
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
# Esto se hace antes de copiar el codigo para aprovechar cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo fuente al contenedor
COPY . .

# Exponer el puerto donde corre Flask
EXPOSE 5000

# Comando para iniciar la aplicacion
CMD ["python", "run.py"]
