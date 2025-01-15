import logging
from psycopg2.extras import RealDictCursor

class WeatherAnalytics:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_extremes(self, city_name: str, parameter: str) -> dict:
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        MIN({}) as min_value,
                        MAX({}) as max_value
                    FROM daily_weather dw
                    JOIN locations l ON dw.location_id = l.location_id
                    WHERE l.city_name = %s;
                """.format(parameter, parameter)
                
                cur.execute(query, [city_name])
                return cur.fetchone()

        except Exception as e:
            logging.error(f"Error getting extremes for {parameter}: {e}")
            raise

    def get_average(self, city_name: str, parameter: str) -> float:
        """Get average value for any parameter from daily_weather"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        AVG({}) as avg_value
                    FROM daily_weather dw
                    JOIN locations l ON dw.location_id = l.location_id
                    WHERE l.city_name = %s;
                """.format(parameter)
                
                cur.execute(query, [city_name])
                result = cur.fetchone()
                return float(result['avg_value']) if result['avg_value'] else None

        except Exception as e:
            logging.error(f"Error getting average for {parameter}: {e}")
            raise