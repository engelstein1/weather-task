import json
import logging
import os
import urllib.request
from typing import Dict, Any

from dotenv import load_dotenv

from src.database.connection import get_connection


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def insert_location(weather_data: Dict[str, Any]) -> int:
    """Insert location data and return the location_id"""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT location_id FROM locations WHERE city_name = %s",
            (weather_data['resolvedAddress'],)
        )
        existing_location = cursor.fetchone()
        
        if existing_location:
            return existing_location[0]
            
        query = """
        INSERT INTO locations (city_name, latitude, longitude, timezone)
        VALUES (%s, %s, %s, %s)
        RETURNING location_id;
        """
        cursor.execute(query, (
            weather_data['resolvedAddress'],
            weather_data['latitude'],
            weather_data['longitude'],
            weather_data['timezone']
        ))
        location_id = cursor.fetchone()[0]
        connection.commit()
        return location_id

    except Exception as e:
        logger.error(f"Error inserting location: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

def insert_daily_weather(location_id: int, day_data: Dict[str, Any]) -> tuple[int, bool]:
    """
    Insert daily weather data and return (daily_id, is_new_record)
    Returns the daily_id and whether this was a new insert
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        cursor.execute(
            "SELECT daily_id FROM daily_weather WHERE location_id = %s AND date = %s",
            (location_id, day_data['datetime'])
        )
        existing_daily = cursor.fetchone()
        
        if existing_daily:
            return existing_daily[0], False  
        query = """
        INSERT INTO daily_weather (
            location_id, date, temp_max, temp_min, humidity,
            wind_speed, wind_gust, wind_dir, precipitation,
            uv_index, cloud_cover, dew, conditions
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING daily_id;
        """
        cursor.execute(query, (
            location_id,
            day_data['datetime'],
            day_data['tempmax'],
            day_data['tempmin'],
            day_data['humidity'],
            day_data['windspeed'],
            day_data.get('windgust', 0),
            day_data['winddir'],
            day_data['precip'],
            day_data['uvindex'],
            day_data['cloudcover'],
            day_data['dew'],
            day_data['conditions']
        ))
        daily_id = cursor.fetchone()[0]
        connection.commit()
        return daily_id, True  

    except Exception as e:
        logger.error(f"Error inserting daily weather: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()


def insert_hourly_weather(daily_id: int, date: str,hours_data: list) -> bool:
    """Insert hourly weather data in bulk for a single day"""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        query = """
        INSERT INTO hourly_weather (
            daily_id, datetime, temp, humidity, wind_speed,
            wind_gust, wind_dir, cloud_cover, conditions
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        data_to_insert = [
            (
                daily_id,
                f"{date} {hour['datetime']}",  
                hour['temp'],
                hour['humidity'],
                hour['windspeed'],
                hour.get('windgust', 0),
                hour['winddir'],
                hour['cloudcover'],
                hour['conditions']
            )
            for hour in hours_data
        ]
        
        cursor.executemany(query, data_to_insert)
        connection.commit()
        return True

    except Exception as e:
        logger.error(f"Error inserting hourly weather: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()


def process_weather_data(weather_data: Dict[str, Any]) -> bool:
    try:
        location_id = insert_location(weather_data)
        logger.info(f"Processing data for location_id: {location_id}")

        for day in weather_data['days']:
            daily_id, is_new_record = insert_daily_weather(location_id, day)
            
            if not is_new_record:
                logger.info(f"Skipping {day['datetime']} - already exists")
                continue
                
            logger.info(f"Processing new daily weather for {day['datetime']}")
            
            hourly_data = day['hours']
            
            if not insert_hourly_weather(daily_id,day['datetime'],hourly_data):
                logger.error(f"Failed to insert hourly weather for {day['datetime']}")

        return True

    except Exception as e:
        logger.error(f"Error processing weather data: {e}")
        return False


def get_weather_data():

    # api_key = "os.getenv("API_KEY_WEATHER")"
    api_key = os.getenv("API_KEY_WEATHER2")

    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Los%20angeles/tomorrow?unitGroup=metric&key={api_key}&contentType=json"
    try:
        ResultBytes = urllib.request.urlopen(url)
        weather_data = json.load(ResultBytes)
        return process_weather_data(weather_data)
    
    except urllib.error.HTTPError as e:
        error_info = e.read().decode() 
        logger.error(f"HTTP Error fetching weather data: {e.code} - {error_info}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data: {e}")
        return False
