import { NavLink, Outlet } from 'react-router-dom'

const navLinkClass = ({ isActive }) =>
  `px-3 py-2 text-sm font-medium rounded-md transition-colors ${
    isActive ? 'text-brand-black bg-brand-surface' : 'text-brand-ink hover:text-brand-black hover:bg-brand-surface'
  }`

export default function AppLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <header className="border-b border-brand-border bg-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <NavLink to="/" className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-brand-black">
              TRI AI <span className="text-brand-gold">Match</span>
            </span>
          </NavLink>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>Jobs</NavLink>
            <NavLink to="/saved-jobs" className={navLinkClass}>Saved Jobs</NavLink>
            <NavLink to="/cv" className={navLinkClass}>My CV</NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-brand-border py-6 mt-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-xs text-brand-ink/70">
          TRI AI Match — estimated CV-to-job compatibility, not a guarantee of an interview or offer.
        </div>
      </footer>
    </div>
  )
}
