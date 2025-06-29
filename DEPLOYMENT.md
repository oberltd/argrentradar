# Deployment Guide - Argentina Real Estate Parser

## 🚀 Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone <repository-url>
cd argentina_real_estate_parser

# Install dependencies
pip install -r requirements.txt

# Initialize database
python main.py init-db

# Start the API server
python main.py api

# Access the application
# Dashboard: http://localhost:12000/
# API Docs: http://localhost:12000/docs
```

### 2. Production Deployment

#### Using Docker (Recommended)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 12000

CMD ["python", "main.py", "api"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "12000:12000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/argentina_real_estate
      - API_HOST=0.0.0.0
      - API_PORT=12000
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=argentina_real_estate
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

#### Using systemd (Linux)

```ini
# /etc/systemd/system/argentina-real-estate.service
[Unit]
Description=Argentina Real Estate Parser
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/argentina_real_estate_parser
Environment=PATH=/opt/argentina_real_estate_parser/venv/bin
ExecStart=/opt/argentina_real_estate_parser/venv/bin/python main.py api
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable argentina-real-estate
sudo systemctl start argentina-real-estate
sudo systemctl status argentina-real-estate
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/argentina_real_estate

# API Configuration
API_HOST=0.0.0.0
API_PORT=12000
API_DEBUG=False

# Scraping Configuration
SCRAPING_DELAY=2
MAX_CONCURRENT_REQUESTS=5
USER_AGENT_ROTATION=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Security
SECRET_KEY=your-secret-key-here
```

### Database Setup

#### PostgreSQL (Production)

```sql
-- Create database and user
CREATE DATABASE argentina_real_estate;
CREATE USER argentina_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE argentina_real_estate TO argentina_user;
```

#### SQLite (Development)

```bash
# Database will be created automatically
python main.py init-db
```

## 🌐 Reverse Proxy Setup

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/argentina-real-estate
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:12000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/argentina_real_estate_parser/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring

### Health Checks

```bash
# API health check
curl http://localhost:12000/health

# Database connectivity
curl http://localhost:12000/api/v1/statistics/overview
```

### Logging

```python
# Custom logging configuration
import logging
from loguru import logger

# Configure loguru
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)
```

### Metrics Collection

```python
# Add to main.py for Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔄 Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="argentina_real_estate"

# PostgreSQL backup
pg_dump -h localhost -U argentina_user $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

### Data Export

```python
# export_data.py
import json
from src.database import db_manager
from src.services import PropertyService

def export_properties():
    with db_manager.get_session() as db:
        property_service = PropertyService(db)
        properties = property_service.search_properties()
        
        data = []
        for prop in properties.properties:
            data.append({
                "id": prop.id,
                "title": prop.title,
                "price": prop.price_amount,
                "currency": prop.price_currency,
                "location": f"{prop.city}, {prop.neighborhood}",
                "source": prop.source_website,
                "url": prop.source_url
            })
        
        with open(f"export_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    export_properties()
```

## 🔐 Security

### API Security

```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/properties/")
@limiter.limit("100/minute")
async def search_properties(request: Request, ...):
    # Your endpoint logic
    pass
```

## 📈 Performance Optimization

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_properties_location ON properties(city, neighborhood);
CREATE INDEX CONCURRENTLY idx_properties_price_range ON properties(price_amount, price_currency);
CREATE INDEX CONCURRENTLY idx_properties_features ON properties(bedrooms, bathrooms);
```

### Caching

```python
# Add Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check database status
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U argentina_user -d argentina_real_estate
   ```

2. **Port Already in Use**
   ```bash
   # Find process using port
   sudo lsof -i :12000
   
   # Kill process
   sudo kill -9 <PID>
   ```

3. **Permission Denied**
   ```bash
   # Fix file permissions
   sudo chown -R www-data:www-data /opt/argentina_real_estate_parser
   sudo chmod -R 755 /opt/argentina_real_estate_parser
   ```

4. **Memory Issues**
   ```bash
   # Monitor memory usage
   htop
   
   # Adjust scraping concurrency
   export MAX_CONCURRENT_REQUESTS=3
   ```

### Log Analysis

```bash
# View application logs
tail -f logs/app.log

# Search for errors
grep -i error logs/app.log

# Monitor API requests
grep "GET\|POST" logs/app.log | tail -20
```

## 📞 Support

For deployment issues:
1. Check the logs first
2. Verify configuration
3. Test database connectivity
4. Check network/firewall settings
5. Create an issue on GitHub with logs and configuration details