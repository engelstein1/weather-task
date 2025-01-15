# weather_import.py
import json
import logging
from pathlib import Path
from typing import Dict, Any
from database import get_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_location(weather_data: Dict[str, Any]) -> int:
    """Insert location data and return the location_id"""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # Check if location exists
        cursor.execute(
            "SELECT location_id FROM locations WHERE city_name = %s",
            (weather_data['resolvedAddress'],)
        )
        existing_location = cursor.fetchone()
        
        if existing_location:
            return existing_location[0]
            
        # Insert new location
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
        
        # Check if daily record exists
        cursor.execute(
            "SELECT daily_id FROM daily_weather WHERE location_id = %s AND date = %s",
            (location_id, day_data['datetime'])
        )
        existing_daily = cursor.fetchone()
        
        if existing_daily:
            return existing_daily[0], False  # Return ID and False for existing record
        
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
        return daily_id, True  # Return ID and True for new record

    except Exception as e:
        logger.error(f"Error inserting daily weather: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

def insert_hourly_weather(daily_id: int, hour_data: Dict[str, Any], date: str) -> bool:
    """Insert hourly weather data"""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        datetime_str = f"{date} {hour_data['datetime']}"
        
        # No need to check - if we got here, we know we need to insert
        query = """
        INSERT INTO hourly_weather (
            daily_id, datetime, temp, humidity, wind_speed,
            wind_gust, wind_dir, cloud_cover, conditions
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (
            daily_id,
            datetime_str,
            hour_data['temp'],
            hour_data['humidity'],
            hour_data['windspeed'],
            hour_data.get('windgust', 0),
            hour_data['winddir'],
            hour_data['cloudcover'],
            hour_data['conditions']
        ))
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
            # Only insert hourly data for new daily records
            for hour in day['hours']:
                if not insert_hourly_weather(daily_id, hour, day['datetime']):
                    logger.error(f"Failed to insert hourly weather for {day['datetime']} {hour['datetime']}")

        return True

    except Exception as e:
        logger.error(f"Error processing weather data: {e}")
        return False

def import_weather_from_file(file_path: str) -> bool:
    """Import weather data from a JSON file into the database"""
    try:
        # Check if file exists
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return False
            
        # Read JSON file
        logger.info(f"Reading weather data from {file_path}")
        with open(file_path, 'r') as file:
            weather_data = json.load(file)
            
        # Log basic information
        days_count = len(weather_data.get('days', []))
        logger.info(f"Found {days_count} days of weather data for {weather_data.get('resolvedAddress', 'unknown location')}")
        
        # Process the weather data
        return process_weather_data(weather_data)
            
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error importing weather data: {e}")
        return False

if __name__ == "__main__":
    # This allows you to run the script directly
    import sys
    
    # Use command line argument if provided, otherwise use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else "weather_data.json"
    
    if import_weather_from_file(file_path):
        print("Weather data imported successfully!")
    else:
        print("Failed to import weather data. Check the logs for details.")
        sys.exit(1)