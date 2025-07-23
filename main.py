from typing import Union
from fastapi import FastAPI

app = FastAPI()
@app.get("/")
def read_root():
    return {"AppStatus": "Woking"}

@app.get("/weatherstation/updateweatherstation.php")
def read_local_weather(ID:str,PASSWORD:str,dateutc:str,baromin:str,tempf:str,humidity:str,dewptf:str,rainin:str,dailyrainin:str,winddir:str,windspeedmph:str,windgustmph:str,UV:str,solarRadiation:str):
    file = open("results.txt","a+")
    data2137 = f"{ID},{PASSWORD},{dateutc},{baromin},{tempf},{humidity},{dewptf},{rainin},{dailyrainin},{winddir},{windspeedmph},{windgustmph},{UV},{solarRadiation}"
    file.write(data2137)
    return {ID,PASSWORD,dateutc,baromin,tempf,humidity,dewptf,rainin,dailyrainin,winddir,windspeedmph,windgustmph,UV,solarRadiation}

