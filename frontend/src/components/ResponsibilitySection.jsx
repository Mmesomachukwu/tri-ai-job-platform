/**
 * The backend returns `responsibility_alignment` as the list of job
 * responsibility lines that ARE supported by CV evidence (see
 * app/services/matching_service.py:_responsibility_scoring). To show
 * "Needing Stronger Evidence" without inventing anything, this splits the
 * job's own `responsibilities` text the same way the backend does (by
 * sentence) and shows whichever lines are NOT already in the aligned set -
 * every word displayed still comes verbatim from the real job posting.
 */
function splitResponsibilities(text) {
  if (!text) return []
  return text.split('.').map((s) => s.trim()).filter(Boolean)
}

export default function ResponsibilitySection({ jobResponsibilities, alignment }) {
  const allLines = splitResponsibilities(jobResponsibilities)
  const alignedSet = new Set(alignment)
  const needsEvidence = allLines.filter((line) => !alignedSet.has(line))

  if (allLines.length === 0) {
    return <p className="text-sm text-brand-ink/60">No structured responsibilities were available for this job.</p>
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-sm font-semibold text-brand-black mb-2 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-green-600" /> Responsibilities You Demonstrate
        </h2>
        {alignment.length === 0 ? (
          <p className="text-sm text-brand-ink/60">
            No strong evidence of these specific responsibilities was found in your CV text.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {alignment.map((line, i) => (
              <li key={i} className="text-sm text-brand-ink flex gap-2">
                <span className="text-green-600">✓</span>{line}.
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-brand-black mb-2 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-brand-orange" /> Responsibilities Needing Stronger Evidence
        </h2>
        {needsEvidence.length === 0 ? (
          <p className="text-sm text-brand-ink/60">Your CV shows evidence for all listed responsibilities.</p>
        ) : (
          <ul className="space-y-1.5">
            {needsEvidence.map((line, i) => (
              <li key={i} className="text-sm text-brand-ink flex gap-2">
                <span className="text-brand-orange">△</span>{line}.
              </li>
            ))}
          </ul>
        )}
        <p className="text-xs text-brand-ink/50 mt-2">
          This means the responsibility isn&apos;t strongly demonstrated in the current CV text - not that you can&apos;t do it.
        </p>
      </section>
    </div>
  )
}
