# ⚽ World Cup Realtime Analytics

Real-time analysis platform for FIFA World Cup matches with a scalable, clean architecture.

## Architecture Overview

```
worldcup-realtime-analytics/
├── backend/           # FastAPI core API
│   ├── app/
│   │   ├── api/       # HTTP routes & WebSocket endpoints
│   │   ├── core/      # Config, security, dependencies
│   │   ├── domain/    # Business entities & interfaces
│   │   ├── services/  # Application use cases
│   │   ├── infra/     # DB, cache, external APIs
│   │   └── workers/   # Background tasks (Celery)
├── ingestion/         # Real-time data ingestion pipeline
├── ml/                # ML models for predictions & stats
├── frontend/          # Next.js dashboard
├── infra/             # Docker, Kubernetes, Terraform
└── docs/              # Architecture documentation
```

## Features

- 📡 **Real-time match events** via WebSockets
- 📊 **Live statistics**: possession, shots, xG, heatmaps
- 🤖 **ML predictions**: match outcome, next goal probability
- 🏟️ **Multi-match support**: follow all World Cup games simultaneously
- 📱 **Responsive dashboard**: desktop + mobile
- 🔄 **Event sourcing**: full audit trail of match events
- ⚡ **Redis Pub/Sub**: low-latency event broadcast
- 🐘 **PostgreSQL + TimescaleDB**: time-series match data

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.115+ |
| Real-time | WebSockets + Redis Pub/Sub |
| Data ingestion | Apache Kafka (optional) / direct polling |
| Database | PostgreSQL + TimescaleDB |
| Cache | Redis 7 |
| ML | scikit-learn + pandas + numpy |
| Frontend | Next.js 15 + TailwindCSS |
| Container | Docker + Docker Compose |
| Deploy | Railway / Render / AWS ECS |
| CI/CD | GitHub Actions |

## Quick Start

```bash
# Clone
git clone https://github.com/Larios4212/worldcup-realtime-analytics.git
cd worldcup-realtime-analytics

# Start all services
docker compose up -d

# Backend available at http://localhost:8000
# Frontend available at http://localhost:3000
# API docs at http://localhost:8000/docs
```

## Development Setup

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/matches` | List all World Cup matches |
| GET | `/matches/{id}` | Match details + live stats |
| GET | `/matches/{id}/timeline` | Full event timeline |
| WS | `/ws/matches/{id}` | Live match events stream |
| GET | `/stats/teams/{id}` | Team statistics |
| GET | `/stats/players/{id}` | Player statistics |
| GET | `/predictions/{id}` | ML predictions for match |

## License

MIT
