export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-brand-ink">
      <span className="h-4 w-4 rounded-full border-2 border-brand-gold border-t-transparent animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="card p-6 text-center max-w-lg mx-auto">
      <p className="text-sm text-brand-black font-medium mb-1">Something went wrong</p>
      <p className="text-sm text-brand-ink/80 mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-outline">
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, message, action }) {
  return (
    <div className="text-center py-16">
      <p className="text-base font-medium text-brand-black mb-1">{title}</p>
      {message && <p className="text-sm text-brand-ink/70 mb-4">{message}</p>}
      {action}
    </div>
  )
}
