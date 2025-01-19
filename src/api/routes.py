import logging
from typing import Dict, Optional
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException, Depends, Query

from src.database.db_initializer import initialize_database
from src.database.connection import get_connection
from src.services.weather_analytics_service import WeatherAnalytics  
from src.services.fire_danger_analytics_service import FireDangerAnalytics 


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        yield conn
    finally:
        conn.close()

def get_analytics(conn = Depends(get_db)):
    return WeatherAnalytics(conn)

@router.get("/")
async def check_connection():
    return {"message": "Welcome to Weather API"}


@router.get("/weather/extremes/{city}/{parameter}")
async def get_extremes(
    city: str, 
    parameter: str,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    analytics: WeatherAnalytics = Depends(get_analytics)
) -> Dict:
    """
    Get min and max values for a weather parameter in a city, optionally within a date range
    
    Parameters:
    - city: City name
    - parameter: Weather parameter (temp_max, temp_min, humidity, etc.)
    - start_date: Optional start date (YYYY-MM-DD)
    - end_date: Optional end date (YYYY-MM-DD)
    """
    try:
        if (start_date and not end_date) or (end_date and not start_date):
            raise HTTPException(
                status_code=400,
                detail="Both start_date and end_date must be provided together"
            )
            
        if start_date and end_date:
            if not analytics.validate_dates(start_date, end_date):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format or range. Use YYYY-MM-DD format and ensure start_date <= end_date"
                )

        result = analytics.get_extremes(city, parameter, start_date, end_date)
        if result['min_value'] is None and result['max_value'] is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {city} {parameter} in specified date range"
            )
            
        response = {
            "city": city,
            "parameter": parameter,
            **result
        }
        if start_date and end_date:
            response.update({
                "start_date": start_date,
                "end_date": end_date
            })
            
        return response

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
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    analytics: WeatherAnalytics = Depends(get_analytics)
) -> Dict:
    """
    Get average value for a weather parameter in a city, optionally within a date range
    
    Parameters:
    - city: City name
    - parameter: Weather parameter (temp_max, temp_min, humidity, etc.)
    - start_date: Optional start date (YYYY-MM-DD)
    - end_date: Optional end date (YYYY-MM-DD)
    """
    try:
        if (start_date and not end_date) or (end_date and not start_date):
            raise HTTPException(
                status_code=400,
                detail="Both start_date and end_date must be provided together"
            )
            
        if start_date and end_date:
            if not analytics.validate_dates(start_date, end_date):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format or range. Use YYYY-MM-DD format and ensure start_date <= end_date"
                )

        result = analytics.get_average(city, parameter, start_date, end_date)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {city} {parameter} in specified date range"
            )

        response = {
            "city": city,
            "parameter": parameter,
            "average": result
        }
        if start_date and end_date:
            response.update({
                "start_date": start_date,
                "end_date": end_date
            })
        return response

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
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT city_name FROM locations ORDER BY city_name")
            cities = [row['city_name'] for row in cur]
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
    

def get_fire_analytics(conn = Depends(get_db)):
    return FireDangerAnalytics(conn)

@router.get("/weather/fire-danger/{city}")
async def get_fire_danger(
    city: str,
    fire_analytics: FireDangerAnalytics = Depends(get_fire_analytics)
) -> Dict:
    """
    Get fire danger ratings for all days in a city
    
    Parameters:
    - city: City name
    """
    try:
        result = fire_analytics.get_fire_danger_by_date(city)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {city}"
            )
        return {"city": city, "fire_danger_ratings": result}
    except Exception as e:
        logger.error(f"Error in get_fire_danger: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/high-fire-risk/{city}")
async def get_high_risk_days(
    city: str,
    fire_analytics: FireDangerAnalytics = Depends(get_fire_analytics)
) -> Dict:
    """
    Get only high risk fire danger days for a city
    
    Parameters:
    - city: City name
    """
    try:
        result = fire_analytics.get_high_risk_days(city)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No high risk days found for {city}"
            )
        return {"city": city, "high_risk_days": result}
    except Exception as e:
        logger.error(f"Error in get_high_risk_days: {e}")
        raise HTTPException(status_code=500, detail=str(e))    

@router.put("/init")
async def startup_event():
    try:
        initialize_database()
        return {"message": "Database initialization completed successfully"}
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise HTTPException(status_code=500, detail="Database initialization failed")
