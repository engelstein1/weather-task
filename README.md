# Weather-task
# Weather Data Service

A robust weather data service that currently imports and analyzes weather data for Los Angeles, with plans to expand to multiple cities worldwide. Built with FastAPI, PostgreSQL, and deployed on Azure Kubernetes Service (AKS).

## Why Los Angeles?

Los Angeles was specifically chosen as the initial city for this service due to the recent wildfires in Southern California, including significant fire activity in the LA and California region over the past two weeks. This makes the fire danger analytics feature particularly relevant and showcases practical application of weather data analysis for public safety.

## Features

- Imports weather data for Los Angeles using Visual Crossing Weather API
- Stores historical weather data in PostgreSQL database
- Provides REST API endpoints for weather data analysis
- Supports date range queries for all analytics
- Implements min/max and average value calculations
- Calculates and monitors fire danger levels
- Identifies high-risk fire danger days
- Containerized with Docker
- Deployed on Azure Kubernetes Service
- Future support planned for multiple cities

## Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Container**: Docker
- **Cloud**: Azure (AKS)
- **API**: Visual Crossing Weather API
- **Language**: Python 3.9+

## Prerequisites

- Azure CLI
- Docker
- kubectl
- PostgreSQL
- Python 3.9+

## Local Development Setup

1. Clone the repository
```bash
git clone https://github.com/engelstein1/weather-task.git
cd weather-history-service
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
HOST=your_db_host
PORT=your_db_port
DATABASE=your_db_name
DB_USER=your_db_user
PASSWORD=your_db_password
API_KEY_WEATHER=your_visual_crossing_api_key
```

5. Run the application
```bash
uvicorn app:app --reload
```

## Docker Setup

Build and run the Docker container:
```bash
docker build -t weather-service:v1 .
docker run -d -p 8000:8000 weather-service:v1
```

## Azure Deployment

1. Login to Azure:
```bash
az login
```

2. Create resource group and AKS cluster:
```bash
az group create --name weather-data-service-rg --location eastus
az acr create --resource-group weather-data-service-rg --name weatherdataacr2025 --sku Basic
```

3. Create AKS cluster:
```bash
az aks create \
    --resource-group weather-data-service-rg \
    --name weather-data-aks \
    --node-count 1 \
    --enable-addons monitoring \
    --generate-ssh-keys \
    --attach-acr weatherdataacr2025
```

4. Get credentials for kubectl:
```bash
az aks get-credentials --resource-group weather-data-service-rg --name weather-data-aks
```

5. Deploy to Kubernetes:
```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## API Endpoints

### Base Endpoints
- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `GET /cities`: Get list of available cities
- `PUT /init`: Initialize database and import weather data

### Analytics Endpoints

#### Fire Danger Analytics
```bash
# Get fire danger ratings for all days
GET /weather/fire-danger/{city}

# Get only high risk fire danger days
GET /weather/high-fire-risk/{city}
```

Example responses:
```json
// Fire danger ratings
{
    "city": "Los Angeles",
    "fire_danger_ratings": [
        {
            "date": "2024-01-01",
            "danger_level": "moderate"
        },
        // ... more dates
    ]
}

// High risk days
{
    "city": "Los Angeles",
    "high_risk_days": [
        {
            "date": "2024-01-15",
            "danger_level": "high"
        },
        // ... more high risk dates
    ]
}
```

#### Weather Extremes
```bash
GET /weather/extremes/{city}/{parameter}
```
Optional query parameters:
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format

Example:
```bash
# Get temperature extremes for January 2024
GET /weather/extremes/Los%20Angeles/temp_max?start_date=2024-01-01&end_date=2024-01-31
```

#### Weather Averages
```bash
GET /weather/average/{city}/{parameter}
```
Optional query parameters:
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format

Example:
```bash
# Get average humidity for all available dates
GET /weather/average/Los%20Angeles/humidity
```

## Implementation Details

### Database Schema

The application uses three main tables:
- `locations`: Stores city information
- `daily_weather`: Stores daily weather metrics
- `hourly_weather`: Stores hourly weather data

### Weather Data Import

Weather data is imported from Visual Crossing Weather API. The import process:
1. Fetches data for Los Angeles (currently)
2. Processes both daily and hourly data
3. Stores in appropriate database tables

### Data Analysis Features

The service provides various analytical capabilities:
- Min/max values for weather parameters
- Average calculations with optional date ranges
- Historical data tracking
- Full data range or specific period analysis
- Fire danger analysis including:
  - Daily fire danger ratings based on weather conditions
  - High-risk day identification

## Security Considerations

- Database credentials managed through Kubernetes secrets
- Azure Container Registry for secure image storage
- Proper environment variable management
- Azure managed identity for AKS-ACR integration
- Input validation for all date parameters

## Monitoring

The deployment includes:
- Azure Monitor integration
- Kubernetes health probes
- Application logging
- Database connection monitoring

## Future Improvements

- Add more weather data providers
- Implement caching
- Add more analytical features
- Set up automated testing
- Implement CI/CD pipeline

## Author

Yitschak Engelstein

