# Marketplays

Two-sided advertising space marketplace.

- **Buyers** discover and book ad spaces on a live map
- **Sellers** list spaces, manage bookings, earn revenue
- **Admin** manages disputes, commissions, platform health

## Monorepo

| Path | Purpose |
|------|---------|
| `apps/web` | Next.js 15 frontend (Vercel — `marketplays-web`) |
| `apps/api` | FastAPI backend (Vercel — `marketplays-api`) |
| `packages/shared` | Shared TypeScript enums/types |
| `docs/` | Schema, state machine, CIS, filters, Stripe |

## Quick start

```bash
# Frontend
cd apps/web
npm install
npm run dev

# Backend
cd apps/api
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Authoritative rules: see `docs/marketplays_cursor_rules.md` and `.cursor/rules/`.  
Stack research: `docs/research-recommendations.md`.
