# SME Financial Health Assessment Platform (Hackathon Submission)

A lightweight, end-to-end platform for **SME financial health analysis**. Users upload financial documents (CSV/XLSX/PDF exports), and the system generates **KPIs, risk signals, credit readiness insights, recommendations, benchmarking, forecasting**, and an **investor-ready report**.

## Features
- Upload financial data: Sales, Expenses (required) + AR/AP/Loans/Inventory (optional)
- Automated KPI extraction (Revenue, Expense, Margin, DSO/DPO, etc.)
- Risk scoring + credit readiness scoring
- Recommendations (collections, EMI pressure, inventory, cost optimization)
- Benchmarking (industry comparisons)
- Forecasting (simple 6-month forecast)
- Investor-ready report output (Markdown)
- History view (local history / list endpoints can be added)
- Secure design goals: encryption-ready storage, minimal PII, CORS controls

## Tech Stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Data processing: Python (pandas)
- Frontend: React (simple UI)
- Optional AI narrative layer: Gemini / GPT (pluggable)

## API Endpoints (Backend)
- `POST /api/assessments`  
  FormData: `company`, `industry`, `lang`, and files: `sales`, `expenses`, `ar`, `ap`, `loans`, `inventory`, `tax`
- `GET /api/assessments/{id}`  
  Returns stored result JSON + report text
- `GET /api/assessments/{id}/report`  
  Returns report markdown/text
- `GET /api/health`  
  Health check

## Local Setup

### 1) Start PostgreSQL (Docker)
```bash
docker compose up -d
```

### 2) Run Backend (FastAPI)
```bash
# Windows PowerShell example
set DATABASE_URL=postgresql+psycopg2://sme:sme@localhost:5432/sme_finance
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Run Frontend
```bash
cd frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
