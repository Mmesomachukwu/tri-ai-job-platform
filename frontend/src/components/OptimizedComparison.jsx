export default function OptimizedComparison({ version }) {
  const { content } = version
  const hasBulletChanges = content.bullet_changes && content.bullet_changes.length > 0
  const hasRealChanges = hasBulletChanges && content.bullet_changes.some((c) => c.original !== c.optimized)

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-brand-black">Original vs Optimized CV</h2>
        <span className="pill">{content.explanation_source === 'ollama' ? 'AI-assisted' : 'Template mode'}</span>
      </div>

      <p className="text-xs text-brand-ink/70 mb-4">{content.changes_explanation}</p>

      {content.optimized_summary && (
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-brand-black mb-1">Optimized Summary</h3>
          <p className="text-sm text-brand-ink card p-3">{content.optimized_summary}</p>
        </div>
      )}

      {hasBulletChanges ? (
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <h3 className="text-xs font-semibold text-brand-ink/70 mb-2 uppercase tracking-wide">Original CV</h3>
            <div className="space-y-2">
              {content.bullet_changes.map((c, i) => (
                <p key={i} className="text-sm text-brand-ink card p-3">{c.original}</p>
              ))}
            </div>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-brand-gold-dark mb-2 uppercase tracking-wide">Optimized CV</h3>
            <div className="space-y-2">
              {content.bullet_changes.map((c, i) => (
                <p
                  key={i}
                  className={`text-sm card p-3 ${c.original !== c.optimized ? 'border-brand-gold text-brand-black' : 'text-brand-ink'}`}
                >
                  {c.optimized}
                </p>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm text-brand-ink/60">No specific bullet-level changes were identified.</p>
      )}

      {!hasRealChanges && (
        <p className="text-xs text-brand-ink/50 mt-4">
          No wording was rewritten in this pass - connect Ollama for AI-assisted rephrasing (still limited to facts
          already present in your original CV).
        </p>
      )}
    </div>
  )
}
