# LegalMetro — SIH 2026

Online Verification System for Weighing & Measuring Instruments under the Legal Metrology Act, 2009.

**Stack:** HTML + CSS + JS · Python (Flask) · MySQL

## Quick Start (Docker)

```bash
cd legalmetro
docker-compose up -d
docker-compose exec backend python seed.py
```

- Frontend: http://localhost:3000
- Backend API: ://httplocalhost:5000/api
- Public verify: http://localhost:3000/verify.html?id=LM-DL-2025-001001

## Manual Setup

### 1. MySQL

Create database `legalmetro` (or run `schema.sql`).

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
# Edit .env with your MySQL credentials
python seed.py
python run.py
```

### 3. Frontend

Serve the `frontend/` folder on port 3000:

```bash
cd frontend
python -m http.server 3000 --bind 127.0.0.1
```

Or use Live Server / nginx.

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@legalmetro.gov.in | Admin@123 |
| LMO Delhi | lmo.delhi@legalmetro.gov.in | Lmo@123 |
| LMO Mumbai | lmo.mumbai@legalmetro.gov.in | Lmo@123 |
| GATC Delhi | gatc@weightech.in | Gatc@123 |
| Business Owner | sharma@store.com | Owner@123 |
| Business Owner | mehta@petrol.com | Owner@123 |

## Demo Instruments

| ID | Status |
|----|--------|
| LM-DL-2025-001001 | Verified — expiring in 10 days |
| LM-DL-2026-001002 | Inspection scheduled |
| LM-MH-2025-002001 | Verified — 6 months left |
| LM-MH-2024-002002 | Expired |

## Project Structure

```
legalmetro/
├── backend/          Flask API + MySQL
├── frontend/         HTML/CSS/JS pages
├── docker-compose.yml
└── README.md
```

## API Base URL

Configure in `frontend/assets/js/api.js`:

```javascript
const BASE = 'http://localhost:5000/api';
```

## Ministry

Consumer Affairs, Food & Public Distribution — SIH 2026
