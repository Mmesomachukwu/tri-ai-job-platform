import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { listResumes } from '../services/resumes'

export default function ResumePicker({ jobId }) {
  const [resumes, setResumes] = useState(null)
  const [selected, setSelected] = useState('')
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    listResumes()
      .then((data) => {
        setResumes(data)
        const successful = data.find((r) => r.extraction_status === 'success')
        if (successful) setSelected(successful.id)
      })
      .catch((err) => setError(err.message))
  }, [])

  if (error) return <p className="text-sm text-red-700">{error}</p>
  if (resumes === null) return <p className="text-sm text-brand-ink/60">Loading your CVs…</p>

  if (resumes.length === 0) {
    return (
      <div className="card p-4">
        <p className="text-sm text-brand-ink mb-3">Upload a CV before analyzing this job.</p>
        <Link to="/cv" className="btn-gold">Upload CV</Link>
      </div>
    )
  }

  const usable = resumes.filter((r) => r.extraction_status === 'success')

  return (
    <div className="card p-4">
      <label className="block text-sm font-medium text-brand-black mb-2">Choose a CV to analyze</label>
      {usable.length === 0 ? (
        <p className="text-sm text-red-700">
          None of your uploaded CVs could be processed. Please upload a valid PDF or DOCX.
        </p>
      ) : (
        <>
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="w-full border border-brand-border rounded-md px-3 py-2 text-sm mb-3"
          >
            {usable.map((r) => (
              <option key={r.id} value={r.id}>{r.label || r.filename}</option>
            ))}
          </select>
          <button
            className="btn-gold w-full"
            disabled={!selected}
            onClick={() => navigate(`/jobs/${jobId}/analyze/${selected}`)}
          >
            Analyze CV Against This Job
          </button>
        </>
      )}
      <Link to="/cv" className="block text-xs text-brand-ink/60 hover:text-brand-black mt-3">
        Manage CVs / upload a new one
      </Link>
    </div>
  )
}
