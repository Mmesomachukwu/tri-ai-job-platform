import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  searchJobs, syncJobs, JOB_CATEGORIES, REMOTE_TYPES, EMPLOYMENT_TYPES,
  EXPERIENCE_LEVELS, POPULAR_SEARCHES,
} from '../services/jobs'
import { saveJob, unsaveJob } from '../services/savedJobs'
import { ApiError } from '../services/api'
import JobCard from '../components/JobCard'
import { LoadingState, ErrorState, EmptyState } from '../components/StateViews'

export default function HomePage() {
  const [params, setParams] = useSearchParams()
  const [keyword, setKeyword] = useState(params.get('keyword') || '')
  const [filters, setFilters] = useState({
    category: params.get('category') || '',
    remoteType: params.get('remoteType') || '',
    employmentType: params.get('employmentType') || '',
    experienceLevel: params.get('experienceLevel') || '',
  })
  const [page, setPage] = useState(1)

  const [state, setState] = useState({ status: 'idle', data: null, error: null })
  const [syncing, setSyncing] = useState(false)
  const [savingId, setSavingId] = useState(null)

  const runSearch = useCallback(async (opts = {}) => {
    setState({ status: 'loading', data: null, error: null })
    try {
      const result = await searchJobs({
        keyword: opts.keyword ?? keyword,
        category: opts.category ?? filters.category,
        remoteType: opts.remoteType ?? filters.remoteType,
        employmentType: opts.employmentType ?? filters.employmentType,
        experienceLevel: opts.experienceLevel ?? filters.experienceLevel,
        page: opts.page ?? page,
      })
      setState({ status: 'success', data: result, error: null })
    } catch (err) {
      setState({ status: 'error', data: null, error: err })
    }
  }, [keyword, filters, page])

  useEffect(() => {
    runSearch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  function handleSearchSubmit(e) {
    e.preventDefault()
    setPage(1)
    setParams({ keyword })
    runSearch({ page: 1 })
  }

  function handlePopular(term) {
    setKeyword(term)
    setPage(1)
    runSearch({ keyword: term, page: 1 })
  }

  function handleFilterChange(key, value) {
    const next = { ...filters, [key]: value }
    setFilters(next)
    setPage(1)
    runSearch({ ...next, page: 1 })
  }

  async function handleSyncRealJobs() {
    setSyncing(true)
    try {
      await syncJobs(keyword || undefined)
      await runSearch({ page: 1 })
    } catch (err) {
      setState({ status: 'error', data: null, error: err })
    } finally {
      setSyncing(false)
    }
  }

  async function handleSave(job) {
    setSavingId(job.id)
    try {
      await saveJob(job.id)
      await runSearch()
    } finally {
      setSavingId(null)
    }
  }

  async function handleUnsave(job) {
    setSavingId(job.id)
    try {
      await unsaveJob(job.id)
      await runSearch()
    } finally {
      setSavingId(null)
    }
  }

  const isProviderOutage = state.status === 'error' && state.error instanceof ApiError && state.error.status === 503

  return (
    <div>
      {/* Hero */}
      <section className="border-b border-brand-border bg-brand-surface">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold text-brand-black tracking-tight">
            TRI AI <span className="text-brand-gold">Match</span>
          </h1>
          <p className="mt-3 text-lg sm:text-xl font-medium text-brand-ink">
            Find Tech Jobs. Know How Well Your CV Matches.
          </p>
          <p className="mt-3 text-sm text-brand-ink/70 max-w-2xl mx-auto">
            Discover real technical jobs from the internet, compare your CV against a specific role,
            identify relevant gaps, and optimize your CV using only your genuine existing experience.
          </p>

          <form onSubmit={handleSearchSubmit} className="mt-8 flex flex-col sm:flex-row gap-2 max-w-xl mx-auto">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Search technical jobs..."
              className="flex-1 border border-brand-border rounded-md px-4 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-gold/40"
            />
            <button type="submit" className="btn-gold px-6">Find Jobs</button>
          </form>

          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {POPULAR_SEARCHES.map((term) => (
              <button
                key={term}
                onClick={() => handlePopular(term)}
                className="pill hover:bg-white hover:border-brand-gold transition-colors"
              >
                {term}
              </button>
            ))}
          </div>

          <div className="mt-6 flex justify-center gap-3">
            <Link to="/cv" className="btn-outline">Analyze My CV</Link>
            <button onClick={handleSyncRealJobs} disabled={syncing} className="btn-outline">
              {syncing ? 'Fetching real jobs…' : 'Refresh Real Jobs'}
            </button>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Filters */}
        <div className="flex flex-wrap gap-2 mb-6">
          <select
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
            className="border border-brand-border rounded-md px-3 py-1.5 text-sm"
          >
            <option value="">All categories</option>
            {JOB_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select
            value={filters.remoteType}
            onChange={(e) => handleFilterChange('remoteType', e.target.value)}
            className="border border-brand-border rounded-md px-3 py-1.5 text-sm"
          >
            <option value="">Any work arrangement</option>
            {REMOTE_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select
            value={filters.employmentType}
            onChange={(e) => handleFilterChange('employmentType', e.target.value)}
            className="border border-brand-border rounded-md px-3 py-1.5 text-sm"
          >
            <option value="">Any employment type</option>
            {EMPLOYMENT_TYPES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select
            value={filters.experienceLevel}
            onChange={(e) => handleFilterChange('experienceLevel', e.target.value)}
            className="border border-brand-border rounded-md px-3 py-1.5 text-sm"
          >
            <option value="">Any experience level</option>
            {EXPERIENCE_LEVELS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {/* Results */}
        {state.status === 'loading' && <LoadingState label="Searching real tech jobs…" />}

        {state.status === 'error' && isProviderOutage && (
          <ErrorState
            message="Unable to retrieve real jobs right now. Please try again later."
            onRetry={() => runSearch()}
          />
        )}
        {state.status === 'error' && !isProviderOutage && (
          <ErrorState message={state.error.message} onRetry={() => runSearch()} />
        )}

        {state.status === 'success' && state.data.results.length === 0 && (
          <EmptyState
            title="No jobs found"
            message="Try a different search term, or refresh to pull the latest real jobs."
            action={<button onClick={handleSyncRealJobs} className="btn-gold">Refresh Real Jobs</button>}
          />
        )}

        {state.status === 'success' && state.data.results.length > 0 && (
          <>
            <p className="text-xs text-brand-ink/60 mb-4">{state.data.total} jobs found</p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {state.data.results.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onSave={handleSave}
                  onUnsave={handleUnsave}
                  saving={savingId === job.id}
                />
              ))}
            </div>
            <div className="flex justify-center gap-2 mt-8">
              <button
                className="btn-outline"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span className="text-sm text-brand-ink/70 px-2 py-2">Page {page}</span>
              <button
                className="btn-outline"
                disabled={state.data.results.length < 20}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  )
}
