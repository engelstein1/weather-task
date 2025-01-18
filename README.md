# Weather-task
# Weather Data Service

A robust weather data service that imports and analyzes weather data for a random city worldwide. Built with FastAPI, PostgreSQL, and deployed on Azure Kubernetes Service (AKS).

## Features

- Imports weather data for the past 30 days using Visual Crossing Weather API
- Stores historical weather data in PostgreSQL database
- Provides REST API endpoints for weather data analysis
- Containerized with Docker
- Deployed on Azure Kubernetes Service
- Implements min/max and average value calculations

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

- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `GET /weather/extremes/{city}/{parameter}`: Get min/max values for a parameter
- `GET /weather/average/{city}/{parameter}`: Get average value for a parameter
- `GET /cities`: Get list of available cities
- `PUT /init`: Initialize database and import weather data

## Implementation Details

### Database Schema

The application uses three main tables:
- `locations`: Stores city information
- `daily_weather`: Stores daily weather metrics
- `hourly_weather`: Stores hourly weather data

### Weather Data Import

Weather data is imported from Visual Crossing Weather API for the past 30 days. The import process:
1. Fetches data for specified cities
2. Processes both daily and hourly data
3. Stores in appropriate database tables

### Data Analysis

The service provides various analytical capabilities:
- Min/max values for weather parameters
- Average calculations
- Historical data tracking

## Security Considerations

- Database credentials managed through Kubernetes secrets
- Azure Container Registry for secure image storage
- Proper environment variable management
- Azure managed identity for AKS-ACR integration

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

