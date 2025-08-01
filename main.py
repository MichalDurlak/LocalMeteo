from typing import Union

import bcrypt
from dnserver import DNSServer

import sqlite3

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from cachetools import TTLCache
from hashlib import sha256

#Cache for the same records (Vevor sent 3 the same get requests)
request_cache = TTLCache(maxsize=100, ttl=10)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
@app.get("/", status_code=200, response_class=HTMLResponse)
@app.get("/index.html", status_code=200, response_class=HTMLResponse)
@app.get("/app.html", status_code=200, response_class=HTMLResponse)
def app_get(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("app.html",context=context)

@app.get("/login", status_code=200, response_class=HTMLResponse)
def login_get(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("login.html",context=context)

@app.post("/login", status_code=200, response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if user_record_login(username, password):
        response = RedirectResponse(url="/", status_code=302)
        return response
    else:
        # Możesz dodać komunikat o błędzie w przyszłości
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Nieprawidłowy login lub hasło"
        })

@app.get("/register", status_code=200, response_class=HTMLResponse)
def register_get(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("register.html",context=context)

@app.post("/register", status_code=200, response_class=HTMLResponse)
def register_post(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    if username is not None and password is not None and email is not None:
        if user_record_add(username, password, email):
            return templates.TemplateResponse("register.html", {
                "request": request,
                "success": "Użytkownik pomyślnie założony."
            })
        else:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Konto o takim loginie lub emailu jest juz w bazie."
            })
    else:
        # Możesz dodać komunikat o błędzie w przyszłości
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Cos poszlo nie tak. Sprawdz czy na pewno wszystkie dane sa poprawne."
        })


@app.get("/weatherstation/updateweatherstation.php", status_code=200)
def read_local_weather(ID:str,PASSWORD:str,dateutc:str,baromin:float,tempf:float,humidity:int,dewptf:float,rainin:float,dailyrainin:float,winddir:int,windspeedmph:float,windgustmph:float,UV:float,solarRadiation:float):

    key = sha256(dateutc.encode()).hexdigest()
    if key in request_cache:
        raise HTTPException(status_code=429, detail="Too many requests")
    request_cache[key] = True

    weather_record_add(ID,PASSWORD,dateutc,baromin,tempf,humidity,dewptf,rainin,dailyrainin,winddir,windspeedmph,windgustmph,UV,solarRadiation)
    # return {ID,PASSWORD,dateutc,baromin,tempf,humidity,dewptf,rainin,dailyrainin,winddir,windspeedmph,windgustmph,UV,solarRadiation}
    return {"AppStatus": "Working. Record saved in database",
            "Status":"OK",
            "Status_Code":200}


def init_local_database():
    print("Initializing local database")
    con = sqlite3.connect("weather.db")
    cur = con.cursor()

    #CREATE TABLE FOR WEATHER DATA
    cur.execute('''
    CREATE TABLE IF NOT EXISTS weather(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_wunderground STRING,
    password_wunderground STRING,
    dateutc STRING,
    baromin FLOAT,
    tempf FLOAT,
    humidity INT,
    dewptf FLOAT,
    rainin FLOAT,
    dailyrainin FLOAT,
    winddir INT,
    windspeedmph INT,
    windgustmph FLOAT,
    uv FLOAT,
    solarRadiation FLOAT)''')
    con.commit()

    #CREATE TABLE FOR USER
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username STRING UNIQUE,
    password STRING,
    email STRING UNIQUE
    )''')
    con.commit()

    con.close()


def user_record_add(username:str,password:str,email:str) -> bool:
    try:
        con = sqlite3.connect("weather.db")
        cur = con.cursor()

        cur.execute('''
        INSERT INTO users(
        username,
        password,
        email
        )
        VALUES (?,?,?)
        ''', (username,hash_password(password),email))
        con.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Błąd dodawania użytkownika: {e}")
        return False

    finally:
        con.close()

def user_record_login(username:str,password:str) -> bool:
    con = sqlite3.connect("weather.db")
    cur = con.cursor()

    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cur.fetchone()

    con.close()

    if result is None:
        # Użytkownik nie istnieje
        return False

    hashed_password = result[0]

    # Sprawdzenie hasła z użyciem bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def weather_record_add(id_wunderground,password_wunderground,dateutc,baromin,tempf,humidity,dewptf,rainin,dailyrainin,winddir,windspeedmph,windgustmph,UV,solarRadiation):
    con = sqlite3.connect("weather.db")
    cur = con.cursor()

    cur.execute('''
    INSERT INTO weather(    
    id_wunderground,
    password_wunderground,
    dateutc,
    baromin,
    tempf,
    humidity,
    dewptf,
    rainin,
    dailyrainin,
    winddir,
    windspeedmph,
    windgustmph,
    uv,
    solarRadiation )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (id_wunderground,hash_password(password_wunderground),dateutc,baromin,tempf,humidity,dewptf,rainin,dailyrainin,winddir,windspeedmph,windgustmph,UV,solarRadiation))
    con.commit()
    con.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(14)).decode()

def main():
    init_local_database()

    server = DNSServer.from_toml('dns_records.toml', port=53)
    server.start()
    assert server.is_running

    uvicorn.run(app, host="0.0.0.0", port=80)

if __name__ == "__main__":
    main()
