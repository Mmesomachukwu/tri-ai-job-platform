import { useEffect, useState } from 'react'
import { getSavedJobs, unsaveJob } from '../services/savedJobs'
import { LoadingState, ErrorState, EmptyState } from '../components/StateViews'
import JobCard from '../components/JobCard'
import { Link } from 'react-router-dom'

export default function SavedJobsPage() {
  const [state, setState] = useState({ status: 'loading', jobs: [], error: null })

  function load() {
    setState((s) => ({ ...s, status: 'loading' }))
    getSavedJobs()
      .then((jobs) => setState({ status: 'success', jobs: jobs.map((j) => ({ ...j, is_saved: true })), error: null }))
      .catch((error) => setState({ status: 'error', jobs: [], error }))
  }

  useEffect(load, [])

  async function handleUnsave(job) {
    await unsaveJob(job.id)
    load()
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="text-2xl font-bold text-brand-black mb-1">Saved Jobs</h1>
      <p className="text-sm text-brand-ink/70 mb-6">Jobs you&apos;ve bookmarked to revisit later.</p>

      {state.status === 'loading' && <LoadingState label="Loading saved jobs…" />}
      {state.status === 'error' && <ErrorState message={state.error.message} onRetry={load} />}
      {state.status === 'success' && state.jobs.length === 0 && (
        <EmptyState
          title="No saved jobs yet"
          message="Save jobs from the search results to see them here."
          action={<Link to="/" className="btn-gold">Search Jobs</Link>}
        />
      )}
      {state.status === 'success' && state.jobs.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {state.jobs.map((job) => (
            <JobCard key={job.id} job={job} onUnsave={handleUnsave} />
          ))}
        </div>
      )}
    </div>
  )
}
