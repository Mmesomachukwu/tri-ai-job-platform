import { useEffect, useRef, useState } from 'react'
import { listResumes, uploadResume, deleteResume, validateFileBeforeUpload } from '../services/resumes'
import { LoadingState, ErrorState, EmptyState } from '../components/StateViews'

export default function CVPage() {
  const [state, setState] = useState({ status: 'loading', resumes: [], error: null })
  const [label, setLabel] = useState('')
  const [uploadState, setUploadState] = useState({ status: 'idle', error: null, fileName: null })
  const fileInputRef = useRef(null)

  function load() {
    setState((s) => ({ ...s, status: 'loading' }))
    listResumes()
      .then((resumes) => setState({ status: 'success', resumes, error: null }))
      .catch((error) => setState({ status: 'error', resumes: [], error }))
  }

  useEffect(load, [])

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return

    const validationError = validateFileBeforeUpload(file)
    if (validationError) {
      setUploadState({ status: 'error', error: validationError, fileName: file.name })
      return
    }

    setUploadState({ status: 'uploading', error: null, fileName: file.name })
    try {
      const resume = await uploadResume(file, label || undefined)
      if (resume.extraction_status === 'failed') {
        setUploadState({ status: 'error', error: resume.extraction_error, fileName: file.name })
      } else {
        setUploadState({ status: 'success', error: null, fileName: file.name })
      }
      setLabel('')
      load()
    } catch (err) {
      setUploadState({ status: 'error', error: err.message, fileName: file.name })
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleDelete(resumeId) {
    await deleteResume(resumeId)
    load()
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="text-2xl font-bold text-brand-black mb-1">My CV</h1>
      <p className="text-sm text-brand-ink/70 mb-6">
        Upload your CV to analyze it against specific tech jobs. Supported formats: PDF, DOCX.
      </p>

      <div className="card p-6 mb-8">
        <label className="block text-sm font-medium text-brand-black mb-1">Label (optional)</label>
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="e.g. Data Science CV"
          className="w-full border border-brand-border rounded-md px-3 py-2 text-sm mb-4"
        />

        <label className="border-2 border-dashed border-brand-border rounded-md flex flex-col items-center justify-center py-10 cursor-pointer hover:border-brand-gold transition-colors">
          <span className="text-sm font-medium text-brand-black">Drag and drop your CV here</span>
          <span className="text-xs text-brand-ink/60 mt-1">or click to choose a file (PDF, DOCX)</span>
          <input ref={fileInputRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleFileChange} />
        </label>

        {uploadState.status === 'uploading' && (
          <p className="text-sm text-brand-ink mt-3">Uploading and parsing {uploadState.fileName}…</p>
        )}
        {uploadState.status === 'success' && (
          <p className="text-sm text-green-700 mt-3">✓ {uploadState.fileName} uploaded successfully.</p>
        )}
        {uploadState.status === 'error' && (
          <p className="text-sm text-red-700 mt-3">
            Could not process {uploadState.fileName}: {uploadState.error}
          </p>
        )}
      </div>

      {state.status === 'loading' && <LoadingState label="Loading your CVs…" />}
      {state.status === 'error' && <ErrorState message={state.error.message} onRetry={load} />}
      {state.status === 'success' && state.resumes.length === 0 && (
        <EmptyState title="No CVs uploaded yet" message="Upload a CV above to get started." />
      )}
      {state.status === 'success' && state.resumes.length > 0 && (
        <div className="space-y-3">
          {state.resumes.map((r) => (
            <div key={r.id} className="card p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-brand-black">{r.label || r.filename}</p>
                <p className="text-xs text-brand-ink/60">
                  {r.filename} · {new Date(r.created_at).toLocaleDateString()} ·{' '}
                  <span className={r.extraction_status === 'success' ? 'text-green-700' : 'text-red-700'}>
                    {r.extraction_status === 'success' ? 'Parsed successfully' : 'Parsing failed'}
                  </span>
                </p>
                {r.extraction_status === 'success' && r.parsed_data?.technical_skills?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {r.parsed_data.technical_skills.slice(0, 8).map((s) => (
                      <span key={s} className="pill">{s}</span>
                    ))}
                  </div>
                )}
              </div>
              <button onClick={() => handleDelete(r.id)} className="btn-outline text-red-700 border-red-200 hover:bg-red-50">
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
