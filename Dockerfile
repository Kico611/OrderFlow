# Koristite Python baziranu sliku
FROM python:3.10-slim

# Postavite radni direktorij
WORKDIR /app

# Kopirajte zahtjeve
COPY requirements.txt .

# Instalirajte zavisnosti
RUN pip install --no-cache-dir -r requirements.txt

# Kopirajte cijelu aplikaciju
COPY ./app /app

# Postavite varijablu okruženja za korijenski direktorij (opcionalno)
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Pokrenite aplikaciju
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



