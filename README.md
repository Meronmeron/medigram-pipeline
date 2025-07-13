# Ethiopian Medical Business Data Platform

A modern data platform for analyzing Ethiopian medical businesses using Telegram data. This platform provides end-to-end ELT pipeline capabilities with ML-powered image analysis to answer business-critical questions about medical products, price trends, posting activity, and image-based content patterns.

## 🎯 Project Overview

This platform enables comprehensive analysis of Ethiopian medical businesses by:

- **Scraping Telegram channels** for health-related messages and images
- **Storing raw JSON data** in a structured data lake
- **Loading data into PostgreSQL** and using dbt for transformations
- **Detecting medical products** in images using YOLOv8
- **Exposing insights** through a FastAPI analytical API
- **Orchestrating the pipeline** using Dagster with scheduling and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │   Data Lake     │    │   PostgreSQL    │
│   Channels      │───▶│   (Raw JSON)    │───▶│   (Warehouse)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   YOLOv8        │    │   dbt           │    │   FastAPI       │
│   Image         │◀───│   (Transform)   │◀───│   (Analytics)   │
│   Analysis      │    └─────────────────┘    └─────────────────┘
└─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dagster       │    │   Redis         │    │   Monitoring    │
│   (Orchestrate) │    │   (Cache)       │    │   & Logging     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Telegram API credentials
- PostgreSQL (handled by Docker)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ethiopian-medical-data-platform
```

### 2. Environment Configuration

Copy the environment template and configure your settings:

```bash
# Create your .env file from template
cp .env.example .env

# Edit .env with your actual values
nano .env
```

**Required Environment Variables:**

- `TELEGRAM_API_ID`: Your Telegram API ID
- `TELEGRAM_API_HASH`: Your Telegram API Hash
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
- `SECRET_KEY`: Application secret key
- `JWT_SECRET_KEY`: JWT signing key

### 3. Start the Platform

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 4. Access Services

- **FastAPI Application**: http://localhost:8000
- **Dagster UI**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📁 Project Structure

```
ethiopian-medical-data-platform/
├── app/                    # Main application code
│   ├── api/               # FastAPI routes and endpoints
│   ├── core/              # Core functionality
│   ├── models/            # Data models and schemas
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── dbt/                   # dbt project for transformations
│   ├── models/            # dbt models
│   ├── macros/            # dbt macros
│   └── profiles/          # dbt profiles
├── data/                  # Data storage
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Processed data
│   └── models/           # ML models
├── scripts/               # Utility scripts
├── tests/                 # Test files
├── logs/                  # Application logs
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Dockerfile           # Application container
├── docker-compose.yml   # Service orchestration
├── .env.example         # Environment template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 🔧 Core Technologies

### Data Collection & Processing

- **Python**: Core programming language
- **Telethon**: Telegram API client
- **python-telegram-bot**: Bot framework
- **BeautifulSoup4**: HTML parsing

### Database & Storage

- **PostgreSQL**: Primary data warehouse
- **Redis**: Caching and session management
- **SQLAlchemy**: ORM and database operations

### Data Transformation

- **dbt**: Data transformation and modeling
- **pandas**: Data manipulation
- **numpy**: Numerical computing

### Machine Learning

- **YOLOv8**: Object detection for medical products
- **OpenCV**: Image processing
- **PyTorch**: Deep learning framework

### API & Web Framework

- **FastAPI**: Modern, fast web framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

### Orchestration

- **Dagster**: Data pipeline orchestration
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration

## 📊 Data Pipeline

### 1. Data Collection

- Scrape public Telegram channels for medical content
- Extract messages, images, and metadata
- Store raw data in JSON format

### 2. Data Storage

- Raw data stored in structured data lake
- PostgreSQL for processed data warehouse
- Redis for caching and session management

### 3. Data Transformation

- dbt models for cleaning and transformation
- Star schema design for analytics
- Data quality checks and validation

### 4. ML Processing

- YOLOv8 model for medical product detection
- Image analysis and classification
- Enrichment of structured data

### 5. API Exposure

- FastAPI endpoints for data access
- Real-time analytics and insights
- RESTful API design

## 🎯 Business Questions Answered

This platform helps answer critical business questions such as:

- **Product Analysis**: What are the most mentioned medical products?
- **Price Trends**: How do medical product prices change over time?
- **Activity Patterns**: When are medical businesses most active?
- **Content Analysis**: What types of images are most common?
- **Market Insights**: Which regions have the highest medical business activity?

## 🔒 Security & Privacy

- Environment variables for sensitive configuration
- JWT-based authentication
- CORS protection
- Input validation and sanitization
- Secure database connections
- Logging and monitoring

## 🧪 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

### Adding New Features

1. **New Data Sources**: Add scrapers in `app/services/scrapers/`
2. **New Models**: Add dbt models in `dbt/models/`
3. **New API Endpoints**: Add routes in `app/api/`
4. **New ML Models**: Add models in `app/services/ml/`

## 📈 Monitoring & Observability

- **Dagster**: Pipeline monitoring and scheduling
- **Logging**: Structured logging with loguru
- **Health Checks**: Service health monitoring
- **Metrics**: Prometheus metrics collection

## 🚀 Deployment

### Production Deployment

```bash
# Set production environment
export ENVIRONMENT=production

# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-Specific Configurations

- **Development**: Local development with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Production deployment with optimizations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

## 🔄 Roadmap

- [ ] Advanced ML models for product classification
- [ ] Real-time streaming data processing
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Mobile application
- [ ] Advanced security features
- [ ] Performance optimizations

---

**Built with ❤️ for Ethiopian Medical Business Intelligence**
