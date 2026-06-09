# 🚀 Global Liquidity Dashboard - Setup Guide

Complete setup guide for the Global Liquidity & Market Correlation Dashboard.

## 📋 Prerequisites

### Required Software
- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** (for cloning the repository)

### Optional (for development)
- **Python 3.10+**
- **PostgreSQL 13+**
- **Redis 6+**

### API Keys (Free)
- **FRED API Key** (required for economic data)
  - Sign up at: https://fred.stlouisfed.org/docs/api/api_key.html
- **CoinGecko Pro API Key** (optional, for higher rate limits)
  - Sign up at: https://www.coingecko.com/en/api/pricing

## 🎯 Quick Start (Recommended)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd global_liquidity_dashboard
```

### 2. Run the Automated Setup
```bash
./scripts/start.sh
```

This script will:
- ✅ Check all requirements
- ✅ Create necessary directories
- ✅ Copy environment configuration
- ✅ Start all services with Docker
- ✅ Wait for services to be ready
- ✅ Display access URLs

### 3. Configure API Keys
Edit the `.env` file and add your API keys:
```bash
FRED_API_KEY=your_fred_api_key_here
COINGECKO_API_KEY=your_coingecko_pro_key_optional
```

### 4. Access the Dashboard
- **📊 Dashboard**: http://localhost:8501
- **🔧 API Documentation**: http://localhost:8000/docs
- **❤️ Health Check**: http://localhost:8000/health

## 🛠️ Manual Setup (Development)

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Start PostgreSQL and Redis
docker run -d --name postgres -e POSTGRES_PASSWORD=replace_with_postgres_password -p 5432:5432 postgres:15
docker run -d --name redis -p 6379:6379 redis:7

# Setup database
python scripts/setup_database.py
```

### 3. Configuration
```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 4. Start Services
```bash
# Terminal 1: Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Streamlit dashboard
streamlit run dashboard/app.py --server.port 8501
```

## 🐳 Docker Deployment

### Production Deployment
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Streamlit     │    │     FastAPI     │
│  Load Balancer  │◄──►│   Dashboard     │◄──►│     Backend     │
│   Port 80/443   │    │   Port 8501     │    │   Port 8000     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                              ┌─────────────────┐      │
                              │     Redis       │◄─────┤
                              │     Cache       │      │
                              │   Port 6379     │      │
                              └─────────────────┘      │
                                                       │
                              ┌─────────────────┐      │
                              │   PostgreSQL    │◄─────┘
                              │    Database     │
                              │   Port 5432     │
                              └─────────────────┘
```

## 🔧 Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/liquidity_dashboard
REDIS_URL=redis://localhost:6379/0

# API Keys
FRED_API_KEY=your_fred_api_key
COINGECKO_API_KEY=your_coingecko_key

# Application
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
UPDATE_FREQUENCY_HOURS=24

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Alerts
ENABLE_ALERTS=True
CORRELATION_ALERT_THRESHOLD=0.2
VOLATILITY_ALERT_THRESHOLD=25.0
```

### Data Sources Configuration
The dashboard automatically collects data from:

1. **CoinGecko API** - Cryptocurrency data
   - Rate limit: 50 calls/minute (free tier)
   - Updates: Every hour

2. **Yahoo Finance** - Traditional market data
   - Rate limit: Unlimited (via yfinance library)
   - Updates: Every 30 minutes during market hours

3. **FRED API** - Economic indicators
   - Rate limit: Generous (requires free API key)
   - Updates: Daily at 9 AM

4. **Alternative.me** - Fear & Greed Index
   - Rate limit: Unlimited
   - Updates: Every 4 hours

## 📊 Dashboard Features

### Main Dashboard
- **📈 Key Metrics**: Real-time prices and changes
- **🚨 Active Alerts**: Correlation breakdowns and volatility spikes
- **🔗 Correlation Heatmap**: Interactive asset correlation matrix
- **💧 Global Liquidity**: Trend analysis and central bank data
- **📊 Performance Charts**: Normalized price comparisons
- **🎯 Risk Metrics**: Volatility and VaR analysis

### Advanced Features
- **🕐 Real-time Updates**: Automatic data refresh
- **📱 Mobile Responsive**: Works on all devices
- **⚡ Fast Loading**: Optimized for performance
- **🎨 Interactive Charts**: Plotly-powered visualizations
- **📊 Data Export**: CSV download capabilities

## 🔍 Monitoring & Maintenance

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health

# Check all containers
docker-compose ps

# View service logs
docker-compose logs -f backend
docker-compose logs -f dashboard
```

### Data Management
```bash
# Manual data collection
curl -X POST http://localhost:8000/api/v1/collect/crypto
curl -X POST http://localhost:8000/api/v1/collect/market

# View collection status
curl http://localhost:8000/api/v1/status
```

### Database Operations
```bash
# Backup database
docker exec liquidity_postgres pg_dump -U postgres liquidity_dashboard > backup.sql

# Restore database
docker exec -i liquidity_postgres psql -U postgres liquidity_dashboard < backup.sql
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :8501

# Kill process or change port in docker-compose.yml
```

#### 2. Database Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker-compose logs postgres
```

#### 3. API Key Issues
```bash
# Verify API keys are set
docker-compose exec backend env | grep API_KEY

# Test FRED API connection
curl "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=YOUR_KEY&file_type=json"
```

#### 4. Memory Issues
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or reduce data collection frequency in .env file
```

### Logs and Debugging
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f dashboard
docker-compose logs -f postgres

# Enable debug mode
# Set DEBUG=True in .env file and restart
```

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose up -d --build
```

### Data Retention
- Market data: 2+ years (configurable)
- Correlation calculations: 1 year
- Risk metrics: 1 year
- Logs: 30 days

### Backup Strategy
- Database: Daily automated backups
- Configuration: Version controlled in Git
- Data exports: Weekly CSV snapshots

## 📚 Additional Resources

### Documentation
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Documentation**: https://docs.streamlit.io/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

### Data Sources
- **FRED API**: https://fred.stlouisfed.org/docs/api/
- **CoinGecko API**: https://www.coingecko.com/en/api/documentation
- **Yahoo Finance**: https://python-yahoofinance.readthedocs.io/

### Support
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Comprehensive guides and tutorials

---

## 🎉 You're All Set!

Your Global Liquidity & Market Correlation Dashboard is now ready to provide real-time insights into financial markets and liquidity conditions.

**Next Steps:**
1. 📊 Explore the dashboard at http://localhost:8501
2. 🔧 Configure alerts and thresholds
3. 📈 Analyze correlations and trends
4. 🚨 Set up monitoring for important market events

**Happy Analyzing! 🌍📊**
