# Xray Control Panel - Backend

FastAPI-based backend for Xray proxy management panel.

## Features

- Multi-user proxy management (VMess, VLESS, Trojan, Shadowsocks)
- Multi-node infrastructure support
- Traffic quota and expiration management
- Subscription generation (V2Ray/Clash/Sing-box/Outline)
- Webhook notifications
- HWID device limiting
- Telegram bot integration
- RESTful API with OpenAPI documentation

## Installation

### Requirements

- Python 3.11+
- PostgreSQL/MySQL/SQLite
- Redis

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Create first admin:
```bash
python -m app.cli admin create --username admin --password your_secure_password --sudo
```

5. Run the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── app/
│   ├── api/            # API endpoints
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── core/           # Core functionality (config, security)
│   ├── db/             # Database setup
│   └── utils/          # Utilities
├── alembic/            # Database migrations
└── tests/              # Tests
```

## Development

Run with hot reload:
```bash
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest
```
