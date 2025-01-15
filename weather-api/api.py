
from fastapi import APIRouter
from database.create_tables import initialize_database
import logging
from fastapi import HTTPException, Depends
from typing import Dict
from database.db_connection import get_connection
from weather_analytics import WeatherAnalytics
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get database connection
def get_db():
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        yield conn
    finally:
        conn.close()

# Dependency to get WeatherAnalytics instance
def get_analytics(conn = Depends(get_db)):
    return WeatherAnalytics(conn)

@router.get("/")
async def check_connection():
    return {"message": "Welcome to Weather API"}


@router.get("/weather/extremes/{city}/{parameter}")
async def get_extremes(
    city: str, 
    parameter: str, 
    analytics: WeatherAnalytics = Depends(get_analytics)
) -> Dict:
    """
    Get min and max values for a weather parameter in a city
    
    Parameters:
    - city: City name
    - parameter: Weather parameter (temp_max, temp_min, humidity, etc.)
    """
    try:
        result = analytics.get_extremes(city, parameter)
        if result['min_value'] is None and result['max_value'] is None:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for {city} {parameter}"
            )
        return result
    except psycopg2.Error as e:
        logger.error(f"Database error in get_extremes: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error in get_extremes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/average/{city}/{parameter}")
async def get_average(
    city: str, 
    parameter: str, 
    analytics: WeatherAnalytics = Depends(get_analytics)
) -> Dict:
    """
    Get average value for a weather parameter in a city
    
    Parameters:
    - city: City name
    - parameter: Weather parameter (temp_max, temp_min, humidity, etc.)
    """
    try:
        result = analytics.get_average(city, parameter)
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for {city} {parameter}"
            )
        return {
            "city": city,
            "parameter": parameter,
            "average": result
        }
    except psycopg2.Error as e:
        logger.error(f"Database error in get_average: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error in get_average: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cities")
async def get_cities(conn = Depends(get_db)):
    """Get list of available cities"""
    try:
        print("Attempting to query cities...")  # Debug print
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT city_name FROM locations ORDER BY city_name")
            cities = [row['city_name'] for row in cur]
            print(f"Found cities: {cities}")  # Debug print
            if not cities:
                raise HTTPException(
                    status_code=404, 
                    detail="No cities found in database"
                )
            return {"cities": cities}
    except psycopg2.Error as e:
        logger.error(f"Database error in get_cities: {e}")
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_cities: {e}")
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

@router.get("/health")
async def health_check(conn = Depends(get_db)) -> Dict:
    """Check if the API and database are healthy"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="System unhealthy")

@router.put("/init")
async def startup_event():
    if not initialize_database():
        logging.error("Failed to initialize database!")
        return {"message": "The init failed!"}
    return {"message": "The init succeeded!"}
