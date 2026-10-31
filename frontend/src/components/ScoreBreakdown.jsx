import { SCORE_COMPONENTS } from '../services/analysis'

function barColor(pct) {
  if (pct >= 75) return 'bg-brand-gold'
  if (pct >= 50) return 'bg-brand-orange'
  return 'bg-brand-border'
}

export default function ScoreBreakdown({ analysis }) {
  return (
    <div className="card p-5">
      <h2 className="text-sm font-semibold text-brand-black mb-4">Score Breakdown</h2>
      <div className="space-y-3">
        {SCORE_COMPONENTS.map(({ key, label }) => {
          const value = analysis[key]
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-brand-ink">{label}</span>
                <span className="font-medium text-brand-black">{value}%</span>
              </div>
              <div className="h-2 rounded-full bg-brand-surface overflow-hidden">
                <div className={`h-full rounded-full ${barColor(value)}`} style={{ width: `${value}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
