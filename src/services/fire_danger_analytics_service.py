import logging

from typing import Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor


class FireDangerAnalytics:
    def __init__(self, db_connection):
        self.conn = db_connection

    def _calculate_danger_rating(self, temp_max: float, wind_speed: float, 
                               humidity: float, precipitation: float) -> str:
        """
        Calculate fire danger rating based on weather parameters
        Returns a string rating: 'Low', 'Moderate', 'High', or 'Extreme'
        """
        danger_score = 0
        
        if temp_max >= 35:
            danger_score += 3  
        elif temp_max >= 28:
            danger_score += 2
        elif temp_max >= 20:
            danger_score += 1

        if wind_speed >= 35:
            danger_score += 3  
        elif wind_speed >= 25:
            danger_score += 2
        elif wind_speed >= 15:
            danger_score += 1

        if humidity <= 30:
            danger_score += 3  
        elif humidity <= 45:
            danger_score += 2
        elif humidity <= 60:
            danger_score += 1

        if precipitation > 5:
            danger_score -= 3
        elif precipitation > 2:
            danger_score -= 2
        elif precipitation > 0:
            danger_score -= 1

        if danger_score >= 7:  
            return "Extreme"
        elif danger_score >= 5:
            return "High"
        elif danger_score >= 3:
            return "Moderate"
        else:
            return "Low"

    def get_fire_danger_by_date(self, city_name: str) -> List[Dict]:
        """
        Analyze fire danger for each day in the database for a specific city
        Returns a list of dictionaries containing date and fire danger rating

        Raises:
            psycopg2.Error: If there's a database-related error
            ValueError: If there's an error processing the data
            Exception: For any other unexpected errors
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        dw.date,
                        dw.temp_max,
                        dw.wind_speed,
                        dw.humidity,
                        dw.precipitation
                    FROM daily_weather dw
                    JOIN locations l ON dw.location_id = l.location_id
                    WHERE l.city_name = %s
                    ORDER BY dw.date DESC;
                """
                
                cur.execute(query, [city_name])
                results = cur.fetchall()
                
                if not results:
                    logging.warning(f"No weather data found for city: {city_name}")
                    return []
                
                fire_danger_ratings = []
                for row in results:
                    try:
                        rating = self._calculate_danger_rating(
                            row['temp_max'],
                            row['wind_speed'],
                            row['humidity'],
                            row['precipitation']
                        )
                        
                        fire_danger_ratings.append({
                            'date': row['date'].strftime('%Y-%m-%d'),
                            'rating': rating,
                            'details': {
                                'temperature': float(row['temp_max']),
                                'wind_speed': float(row['wind_speed']),
                                'humidity': float(row['humidity']),
                                'precipitation': float(row['precipitation']),
                                'risk_factors': self._get_risk_factors(
                                    float(row['temp_max']),
                                    float(row['wind_speed']),
                                    float(row['humidity']),
                                    float(row['precipitation'])
                                )
                            }
                        })
                    except (ValueError, TypeError) as e:
                        logging.error(f"Error processing row data: {e}")
                        continue  
                
                return fire_danger_ratings
                
        except psycopg2.Error as e:
            logging.error(f"Database error in get_fire_danger_by_date: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in get_fire_danger_by_date: {e}")
            raise

    def _get_risk_factors(self, temp: float, wind: float, humidity: float, precip: float) -> List[str]:
        """
        Identify specific risk factors contributing to fire danger
        """
        factors = []
        if temp >= 35:
            factors.append("Extreme temperature")
        elif temp >= 28:
            factors.append("High temperature")
            
        if wind >= 35:
            factors.append("Extreme winds")
        elif wind >= 25:
            factors.append("Strong winds")
            
        if humidity <= 30:
            factors.append("Very low humidity")
        elif humidity <= 45:
            factors.append("Low humidity")
            
        if precip <= 0:
            factors.append("No precipitation")
        
        return factors

    def get_high_risk_days(self, city_name: str) -> List[Dict]:
        """
        Get all days with High or Extreme fire danger rating
        """
        all_ratings = self.get_fire_danger_by_date(city_name)
        return [day for day in all_ratings 
                if day['rating'] in ['High', 'Extreme']]