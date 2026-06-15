"""
Data Ingestion Pipeline
=======================
Polls external sports APIs and feeds live match data into the system.

Supports:
- football-data.org (free tier: 10 req/min)
- api-sports.io / api-football.com (free tier: 100 req/day)

Architecture:
  ┌─────────────────┐     poll     ┌────────────────┐
  │  Sports APIs    │ ──────────► │  Normalizer    │
  └─────────────────┘             └───────┬────────┘
                                          │ normalized events
                                   ┌──────▼──────┐
                                   │  Redis      │
                                   │  Pub/Sub    │
                                   └──────┬──────┘
                                          │
                                   ┌──────▼──────┐
                                   │  PostgreSQL │
                                   └─────────────┘
"""

import asyncio
import os
import sys

# Ensure shared code is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline import IngestionPipeline
from config import IngestionConfig


async def main():
    config = IngestionConfig()
    pipeline = IngestionPipeline(config)
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
