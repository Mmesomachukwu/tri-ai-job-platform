import { Link } from 'react-router-dom'

function formatSalary(min, max) {
  if (!min && !max) return null
  const fmt = (n) => `$${Math.round(n / 1000)}k`
  if (min && max) return `${fmt(min)} – ${fmt(max)}`
  return fmt(min || max)
}

function formatPostedDate(dateStr) {
  if (!dateStr) return null
  const posted = new Date(dateStr)
  const days = Math.floor((Date.now() - posted.getTime()) / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'Posted today'
  if (days === 1) return 'Posted 1 day ago'
  return `Posted ${days} days ago`
}

export default function JobCard({ job, onSave, onUnsave, saving }) {
  const salary = formatSalary(job.salary_min, job.salary_max)
  const posted = formatPostedDate(job.posted_date)
  const skills = [...(job.required_skills || []), ...(job.preferred_skills || [])].slice(0, 6)

  return (
    <div className="card p-5 flex flex-col gap-3">
      <div>
        <Link to={`/jobs/${job.id}`} className="text-base font-semibold text-brand-black hover:text-brand-gold-dark">
          {job.title}
        </Link>
        <p className="text-sm text-brand-ink/80">{job.company}</p>
        <p className="text-xs text-brand-ink/60 mt-0.5">
          {[job.location, job.remote_type].filter(Boolean).join(' · ')}
        </p>
      </div>

      {skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((s) => (
            <span key={s} className="pill">{s}</span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-brand-ink/70">
        <span>{salary || job.employment_type || ''}</span>
        <span>{posted}</span>
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-brand-border">
        <Link to={`/jobs/${job.id}`} className="btn-outline flex-1 text-center">View Job</Link>
        <Link to={`/jobs/${job.id}`} className="btn-gold flex-1 text-center">Analyze CV</Link>
        {(onSave || onUnsave) && (
          <button
            onClick={() => (job.is_saved ? onUnsave?.(job) : onSave?.(job))}
            disabled={saving}
            className="btn-outline px-3"
            title={job.is_saved ? 'Remove from saved' : 'Save job'}
          >
            {job.is_saved ? 'Saved ✓' : 'Save'}
          </button>
        )}
      </div>
    </div>
  )
}
