import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getJob } from '../services/jobs'
import { saveJob, unsaveJob } from '../services/savedJobs'
import { LoadingState, ErrorState } from '../components/StateViews'
import ResumePicker from '../components/ResumePicker'

function formatSalary(min, max) {
  if (!min && !max) return null
  const fmt = (n) => `$${n.toLocaleString()}`
  if (min && max) return `${fmt(min)} – ${fmt(max)}`
  return fmt(min || max)
}

export default function JobDetailsPage() {
  const { id } = useParams()
  const [state, setState] = useState({ status: 'loading', job: null, error: null })
  const [savingState, setSavingState] = useState(false)

  function load() {
    setState({ status: 'loading', job: null, error: null })
    getJob(id)
      .then((job) => setState({ status: 'success', job, error: null }))
      .catch((error) => setState({ status: 'error', job: null, error }))
  }

  useEffect(load, [id])

  async function toggleSave() {
    if (!state.job) return
    setSavingState(true)
    try {
      if (state.job.is_saved) {
        await unsaveJob(state.job.id)
      } else {
        await saveJob(state.job.id)
      }
      load()
    } finally {
      setSavingState(false)
    }
  }

  if (state.status === 'loading') return <LoadingState label="Loading job details…" />
  if (state.status === 'error') {
    const notFound = state.error.status === 404
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <ErrorState
          message={notFound ? 'This job could not be found.' : state.error.message}
          onRetry={notFound ? undefined : load}
        />
      </div>
    )
  }

  const job = state.job
  const salary = formatSalary(job.salary_min, job.salary_max)

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 grid md:grid-cols-3 gap-8">
      <div className="md:col-span-2">
        <p className="text-xs text-brand-ink/60 mb-2">
          <Link to="/" className="hover:text-brand-black">← Back to search</Link>
        </p>
        <h1 className="text-2xl font-bold text-brand-black">{job.title}</h1>
        <p className="text-brand-ink mt-1">{job.company}</p>
        <p className="text-sm text-brand-ink/70 mt-1">
          {[job.location, job.remote_type, job.employment_type].filter(Boolean).join(' · ')}
        </p>
        {salary && <p className="text-sm text-brand-ink mt-1 font-medium">{salary}</p>}
        {job.experience_level && <p className="text-xs text-brand-ink/60 mt-1">{job.experience_level} level</p>}

        {(job.required_skills?.length > 0 || job.preferred_skills?.length > 0) && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {job.required_skills?.map((s) => <span key={s} className="pill">{s}</span>)}
            {job.preferred_skills?.map((s) => (
              <span key={s} className="pill opacity-70">{s} (preferred)</span>
            ))}
          </div>
        )}

        {job.description && (
          <section className="mt-6">
            <h2 className="text-sm font-semibold text-brand-black mb-1">Description</h2>
            <p className="text-sm text-brand-ink/90 whitespace-pre-line">{job.description}</p>
          </section>
        )}
        {job.responsibilities && (
          <section className="mt-6">
            <h2 className="text-sm font-semibold text-brand-black mb-1">Responsibilities</h2>
            <p className="text-sm text-brand-ink/90 whitespace-pre-line">{job.responsibilities}</p>
          </section>
        )}
        {job.requirements && (
          <section className="mt-6">
            <h2 className="text-sm font-semibold text-brand-black mb-1">Requirements</h2>
            <p className="text-sm text-brand-ink/90 whitespace-pre-line">{job.requirements}</p>
          </section>
        )}

        <p className="text-xs text-brand-ink/50 mt-8">Source: {job.source}</p>
      </div>

      <div className="space-y-4">
        <div className="card p-4 space-y-2">
          <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="btn-primary w-full">
            View Original Posting
          </a>
          <button onClick={toggleSave} disabled={savingState} className="btn-outline w-full">
            {job.is_saved ? 'Remove from Saved' : 'Save Job'}
          </button>
        </div>

        <ResumePicker jobId={job.id} />
      </div>
    </div>
  )
}
