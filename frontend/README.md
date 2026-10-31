# TRI AI Match — Frontend

React + JavaScript (JSX) + Vite + Tailwind CSS + React Router. No TypeScript, no Docker.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. In dev, Vite proxies `/api/*` to the FastAPI
backend at `http://localhost:8000` (see `vite.config.js`) — make sure the
backend is running first (`cd ../backend && uvicorn app.main:app --reload`).

## Build

```bash
npm run build   # outputs to dist/
npm run lint    # eslint
```

## Structure

```
src/
├── components/    JobCard, ScoreBreakdown, KeywordSections, ResponsibilitySection,
│                  OptimizedComparison, ResumePicker, StateViews (loading/error/empty)
├── layouts/       AppLayout (header/nav, no auth links)
├── pages/         HomePage, JobDetailsPage, CVPage, AnalysisPage, SavedJobsPage
├── services/      api.js (base client), jobs.js, resumes.js, analysis.js, savedJobs.js
├── App.jsx        routes
└── main.jsx       entry point
```

## Routes

| Path | Page |
|---|---|
| `/` | Search real tech jobs |
| `/jobs/:id` | Job details |
| `/cv` | Upload/manage CVs |
| `/jobs/:jobId/analyze/:resumeId` | CV match analysis + optimization |
| `/saved-jobs` | Saved jobs |

## Notes

- **No authentication** — single-user local app, no login/register anywhere.
- **No mock jobs** — the frontend only ever displays what the backend's
  `RealJobProvider` returns. If the backend can't reach real job sources,
  `POST /jobs/sync` returns a 503 and the UI shows
  *"Unable to retrieve real jobs right now. Please try again later."*
  — never fabricated listings.
- **Match score is never computed client-side.** Every percentage shown
  (`overall_score` and every `*_score` component) is rendered directly
  from the backend's `AnalysisOut` response — the frontend does no scoring.
- **No secrets in this codebase.** The frontend never holds an Ollama URL,
  a job-API key, or a database credential — it only ever calls the FastAPI
  backend at a relative `/api/v1/...` path.
- **Responsibilities Needing Stronger Evidence** is derived client-side by
  diffing the job's own `responsibilities` text against the backend's
  `responsibility_alignment` list (same sentence-splitting the backend
  itself uses) — every word shown still comes from the real job posting,
  nothing is invented.
