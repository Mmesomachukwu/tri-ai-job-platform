import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getJob } from '../services/jobs'
import { getResume, optimizeResume } from '../services/resumes'
import { analyzeResume } from '../services/analysis'
import { LoadingState, ErrorState } from '../components/StateViews'
import ScoreBreakdown from '../components/ScoreBreakdown'
import KeywordSections from '../components/KeywordSections'
import ResponsibilitySection from '../components/ResponsibilitySection'
import OptimizedComparison from '../components/OptimizedComparison'

function scoreRingColor(score) {
  if (score >= 75) return 'text-brand-gold'
  if (score >= 50) return 'text-brand-orange'
  return 'text-brand-ink/60'
}

export default function AnalysisPage() {
  const { jobId, resumeId } = useParams()
  const [state, setState] = useState({ status: 'loading', job: null, resume: null, analysis: null, error: null })
  const [optimizeState, setOptimizeState] = useState({ status: 'idle', version: null, error: null })

  function load() {
    setState((s) => ({ ...s, status: 'loading', error: null }))
    Promise.all([getJob(jobId), getResume(resumeId)])
      .then(([job, resume]) => {
        if (resume.extraction_status !== 'success') {
          setState({ status: 'error', job, resume, analysis: null, error: { message: 'This CV could not be processed. Please upload a valid PDF or DOCX.' } })
          return
        }
        return analyzeResume(resumeId, jobId).then((analysis) => {
          setState({ status: 'success', job, resume, analysis, error: null })
        })
      })
      .catch((error) => setState((s) => ({ ...s, status: 'error', error })))
  }

  useEffect(load, [jobId, resumeId])

  async function handleOptimize() {
    setOptimizeState({ status: 'loading', version: null, error: null })
    try {
      const version = await optimizeResume(resumeId, jobId)
      setOptimizeState({ status: 'success', version, error: null })
    } catch (error) {
      setOptimizeState({ status: 'error', version: null, error })
    }
  }

  if (state.status === 'loading') return <LoadingState label="Analyzing your CV against this role…" />
  if (state.status === 'error') {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <ErrorState message={state.error.message} onRetry={load} />
      </div>
    )
  }

  const { job, analysis } = state
  const findings = analysis.analysis_result.keyword_findings || []
  const alignment = analysis.analysis_result.responsibility_alignment || []

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      <p className="text-xs text-brand-ink/60 mb-2">
        <Link to={`/jobs/${job.id}`} className="hover:text-brand-black">← Back to {job.title}</Link>
      </p>
      <h1 className="text-xl font-bold text-brand-black">{job.title}</h1>
      <p className="text-sm text-brand-ink/70 mb-8">{job.company}</p>

      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-6">
          <div className="card p-6 text-center">
            <p className="text-xs uppercase tracking-wide text-brand-ink/60 mb-2">Your CV Match</p>
            <p className={`text-5xl font-bold ${scoreRingColor(analysis.overall_score)}`}>
              {analysis.overall_score}%
            </p>
            <p className="text-xs text-brand-ink/60 mt-3">
              This is an estimated CV-to-job match score. It is not a guarantee of passing an employer ATS,
              receiving an interview, or getting the job.
            </p>
          </div>

          <ScoreBreakdown analysis={analysis} />

          <div className="card p-5">
            <button onClick={handleOptimize} disabled={optimizeState.status === 'loading'} className="btn-gold w-full">
              {optimizeState.status === 'loading' ? 'Optimizing…' : 'Optimize My CV'}
            </button>
            {optimizeState.status === 'error' && (
              <p className="text-xs text-red-700 mt-2">{optimizeState.error.message}</p>
            )}
          </div>
        </div>

        <div className="md:col-span-2 space-y-8">
          <KeywordSections findings={findings} />

          <ResponsibilitySection jobResponsibilities={job.responsibilities} alignment={alignment} />

          <section>
            <h2 className="text-sm font-semibold text-brand-black mb-2">Recommendations</h2>
            {analysis.recommendations.length === 0 ? (
              <p className="text-sm text-brand-ink/60">No specific recommendations - your CV aligns well with this role.</p>
            ) : (
              <ul className="space-y-2">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i} className="card p-3 text-sm text-brand-ink">{rec}</li>
                ))}
              </ul>
            )}
          </section>

          {optimizeState.status === 'success' && <OptimizedComparison version={optimizeState.version} />}
        </div>
      </div>
    </div>
  )
}
