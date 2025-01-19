import logging
from datetime import datetime
from typing import Optional

from psycopg2.extras import RealDictCursor


class WeatherAnalytics:
    def __init__(self, db_connection):
        self.conn = db_connection


    def get_extremes(self, city_name: str, parameter: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
        """Get min and max values for a parameter, optionally within a date range"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        MIN({}) as min_value,
                        MAX({}) as max_value
                    FROM daily_weather dw
                    JOIN locations l ON dw.location_id = l.location_id
                    WHERE l.city_name = %s
                """.format(parameter, parameter)
                
                params = [city_name]
                
                if start_date and end_date:
                    query += " AND date BETWEEN %s AND %s"
                    params.extend([start_date, end_date])
                
                cur.execute(query, params)
                return cur.fetchone()

        except Exception as e:
            logging.error(f"Error getting extremes for {parameter}: {e}")
            raise

    def get_average(self, city_name: str, parameter: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> float:
        """Get average value for any parameter from daily_weather, optionally within a date range"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        AVG({}) as avg_value
                    FROM daily_weather dw
                    JOIN locations l ON dw.location_id = l.location_id
                    WHERE l.city_name = %s
                """.format(parameter)
                
                params = [city_name]
                
                if start_date and end_date:
                    query += " AND date BETWEEN %s AND %s"
                    params.extend([start_date, end_date])
                
                cur.execute(query, params)
                result = cur.fetchone()
                return float(result['avg_value']) if result['avg_value'] else None

        except Exception as e:
            logging.error(f"Error getting average for {parameter}: {e}")
            raise

    def validate_dates(self, start_date: str, end_date: str) -> bool:
        """Validate date format and range"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            return start <= end
        except ValueError:
            return False