# Sovereign Sentinel

An autonomous Financial War Room system designed to detect Shadow Defaults in corporate debt by monitoring PIK (Payment-in-Kind) loans and cross-referencing them with real-time geopolitical shocks.

## Overview

Sovereign Sentinel employs three specialized agents:
- **OSINT Scout**: Tracks global crises using You.com API
- **Forensic Auditor**: Identifies high-risk PIK toggles in loan data
- **Treasury Commander**: Autonomously triggers Bitcoin hedges via Composio

The system uses a Policy Brain orchestrator (powered by Gemini) to evaluate risk and escalate threats, with an interactive War Room Dashboard for monitoring and manual intervention.

## Project Structure

```
Sovereign-Sentinel/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # FastAPI application
│   │   ├── config.py    # Configuration management
│   │   ├── models.py    # Data models
│   │   ├── you_client.py    # You.com API client
│   │   ├── osint_scout.py   # OSINT Scout agent
│   │   └── scheduler.py     # Scheduled scanning
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Edit `.env` and add your API keys:
```
YOU_API_KEY=your_you_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

6. Run the backend:
```bash
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file:
```bash
cp .env.example .env.local
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Backend API

- `GET /` - Root endpoint with service information
- `GET /health` - Health check endpoint
- `GET /api/risk/latest` - Get the latest risk assessment
- `POST /api/scan/immediate` - Trigger an immediate OSINT scan
- `GET /api/scan/status` - Get scheduler status

## Features Implemented (Task 1)

✅ Backend directory structure with FastAPI application
✅ Frontend directory structure with Next.js application
✅ Environment configuration for API keys (YOU_API_KEY, OPENAI_API_KEY)
✅ You.com API client with error handling and caching
✅ Scheduled scanning with APScheduler (15-minute intervals)
✅ Risk score calculation logic (sentiment analysis + recency weighting)
✅ RiskAssessment and NewsArticle data models

## Next Steps

- Task 2: Implement Forensic Auditor for PIK loan analysis
- Task 3: Build Policy Brain orchestration with Gemini
- Task 4: Create War Room Dashboard with real-time updates
- Task 5: Integrate Plivo voice alert system
- Task 6: Build Treasury Commander with Composio integration
- Task 7: Deploy to Render and configure production environment

## License

Proprietary - All rights reserved

