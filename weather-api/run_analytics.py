from database.db_connection import get_connection
from weather_analytics import WeatherAnalytics

conn = get_connection()

analytics = WeatherAnalytics(conn)

try:

    temp_max = analytics.get_extremes('Los Angeles, CA, United States', 'temp_max')
    print(f"Temperature max range: {temp_max['min_value']} to {temp_max['max_value']}")
    
    humidity = analytics.get_extremes('Los Angeles, CA, United States', 'humidity')
    print(f"Humidity range: {humidity['min_value']} to {humidity['max_value']}")

    avg_temp_max = analytics.get_average('Los Angeles, CA, United States', 'temp_max')
    print(f"Average max temperature: {avg_temp_max}")
    
    avg_humidity = analytics.get_average('Los Angeles, CA, United States', 'humidity')
    print(f"Average humidity: {avg_humidity}")

finally:
    conn.close()