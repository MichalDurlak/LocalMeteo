FROM python:3.12

# Ustaw katalog roboczy
WORKDIR /usr/src/app

# Kopiuj pliki do katalogu roboczego
#TODO: AUTOMATYCZNE TWORZENIE PLIKU DNS_RECORDS.TOMAL
COPY dns_records.toml ./
COPY main.py ./
COPY requirements.txt ./

# Zainstaluj zależności z pliku requirements
RUN pip install --no-cache-dir -r requirements.txt

# Utwórz użytkownika app i ustaw prawa, aby mogl tworzyc pliki
RUN useradd -m app \
    && chown -R app /usr/src/app

# Przełącz się na użytkownika app
USER app

# Uruchom skrypt
CMD ["python", "./main.py"]
