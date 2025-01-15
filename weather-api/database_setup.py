from database import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_query(query, description):
    """
    Execute a database query safely with proper connection handling
    """
    connection = get_connection()
    if not connection:
        logger.error("Failed to establish database connection.")
        return False

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        logger.info(f"Successfully {description}")
        return True

    except Exception as e:
        logger.error(f"Error {description}: {e}")
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()

def create_locations_table():
    """Creates the locations table for storing city information."""
    query = """
    CREATE TABLE IF NOT EXISTS locations (
        location_id SERIAL PRIMARY KEY,
        city_name VARCHAR(100) NOT NULL,
        latitude DECIMAL(9,6) NOT NULL,
        longitude DECIMAL(9,6) NOT NULL,
        timezone VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(city_name)
    );
    """
    return execute_query(query, "created locations table")

def create_daily_weather_table():
    """Creates the daily_weather table for storing daily weather metrics."""
    query = """
    CREATE TABLE IF NOT EXISTS daily_weather (
        daily_id SERIAL PRIMARY KEY,
        location_id INTEGER REFERENCES locations(location_id),
        date DATE NOT NULL,
        temp_max DECIMAL(5,2) NOT NULL,
        temp_min DECIMAL(5,2) NOT NULL,
        humidity DECIMAL(5,2) NOT NULL,
        wind_speed DECIMAL(5,2) NOT NULL,
        wind_gust DECIMAL(5,2),
        wind_dir DECIMAL(5,2),
        precipitation DECIMAL(5,2) DEFAULT 0,
        uv_index DECIMAL(4,2),
        cloud_cover DECIMAL(5,2),
        dew DECIMAL(5,2),
        conditions VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(location_id, date)
    );
    """
    return execute_query(query, "created daily_weather table")

def create_hourly_weather_table():
    """Creates the hourly_weather table for detailed weather tracking."""
    query = """
    CREATE TABLE IF NOT EXISTS hourly_weather (
        hourly_id SERIAL PRIMARY KEY,
        daily_id INTEGER REFERENCES daily_weather(daily_id),
        datetime TIMESTAMP NOT NULL,
        temp DECIMAL(5,2) NOT NULL,
        humidity DECIMAL(5,2) NOT NULL,
        wind_speed DECIMAL(5,2) NOT NULL,
        wind_gust DECIMAL(5,2),
        wind_dir DECIMAL(5,2),
        cloud_cover DECIMAL(5,2),
        conditions VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(daily_id, datetime)
    );
    """
    return execute_query(query, "created hourly_weather table")

def initialize_database():
    """Initialize all database tables in the correct order"""
    logger.info("Starting database initialization...")
    
    # Create tables in order of dependencies
    if create_locations_table():
        if create_daily_weather_table():
            if create_hourly_weather_table():
                logger.info("Database initialization completed successfully!")
                return True
    
    logger.error("Database initialization failed!")
    return False

if __name__ == "__main__":
    initialize_database()