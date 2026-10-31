/**
 * Renders the three KeywordFinding states exactly as the backend produces
 * them - never inventing or re-deriving status client-side. See
 * app/schemas/analysis.py:KeywordFinding for the source of truth.
 */
export default function KeywordSections({ findings }) {
  const demonstrated = findings.filter((f) => f.status === 'demonstrated')
  const strengthen = findings.filter((f) => f.status === 'strengthen')
  const gaps = findings.filter((f) => f.status === 'gap')

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-sm font-semibold text-brand-black mb-2 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-green-600" /> Strong Matches
        </h2>
        {demonstrated.length === 0 ? (
          <p className="text-sm text-brand-ink/60">No strong keyword matches were found for this role.</p>
        ) : (
          <div className="space-y-2">
            {demonstrated.map((f) => (
              <div key={f.term} className="card p-3">
                <p className="text-sm font-medium text-brand-black">{f.term}</p>
                {f.cv_evidence && <p className="text-xs text-brand-ink/70 mt-0.5 italic">&quot;{f.cv_evidence}&quot;</p>}
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-brand-black mb-2 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-brand-orange" /> Keywords to Strengthen
        </h2>
        {strengthen.length === 0 ? (
          <p className="text-sm text-brand-ink/60">No specific wording improvements identified.</p>
        ) : (
          <div className="space-y-2">
            {strengthen.map((f) => (
              <div key={f.term} className="card p-3">
                <p className="text-sm font-medium text-brand-black">{f.term}</p>
                <p className="text-xs text-brand-ink/70 mt-0.5">Currently: &quot;{f.cv_evidence}&quot;</p>
                <p className="text-xs text-brand-gold-dark mt-0.5">Suggestion: {f.suggestion}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-brand-black mb-2 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-red-500" /> Not Currently Demonstrated
        </h2>
        {gaps.length === 0 ? (
          <p className="text-sm text-brand-ink/60">No significant keyword gaps were found for this role.</p>
        ) : (
          <div className="space-y-2">
            {gaps.map((f) => (
              <div key={f.term} className="card p-3">
                <p className="text-sm font-medium text-brand-black">{f.term}</p>
                <p className="text-xs text-brand-ink/70 mt-0.5">
                  Not currently demonstrated in your CV. If you have genuine experience with it, consider adding it.
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
