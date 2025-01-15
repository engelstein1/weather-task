from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import requests
import os
import urllib.request
import sys
import json
from database_setup import initialize_database
# from database import get_db, engine, Base
import database
import logging

load_dotenv()
app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    if not initialize_database():
        logging.error("Failed to initialize database!")

@app.get("/weather/last30days/{city}")
async def get_weather(city):
    print('hi')
    api_key = "HUZLDMPCUMZDGQ5KVRX3SLYSB"
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Los%20angeles/last30days?unitGroup=metric&key=HUZLDMPCUMZDGQ5KVRX3SLYSB&contentType=json"
    
    try: 
        # ResultBytes = urllib.request.urlopen(url)
  
        # data = json.load(ResultBytes)

        return {
            "city": city,
            "data": 'data'
        }
    except urllib.error.HTTPError  as e:
        ErrorInfo= e.read().decode() 
        print('Error code: ', e.code, ErrorInfo)
        sys.exit()
    except  urllib.error.URLError as e:
        ErrorInfo= e.read().decode() 
        print('Error code: ', e.code,ErrorInfo)
        sys.exit()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Weather API"}
