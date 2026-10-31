import { Routes, Route } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import HomePage from './pages/HomePage'
import JobDetailsPage from './pages/JobDetailsPage'
import CVPage from './pages/CVPage'
import AnalysisPage from './pages/AnalysisPage'
import SavedJobsPage from './pages/SavedJobsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/jobs/:id" element={<JobDetailsPage />} />
        <Route path="/cv" element={<CVPage />} />
        <Route path="/jobs/:jobId/analyze/:resumeId" element={<AnalysisPage />} />
        <Route path="/saved-jobs" element={<SavedJobsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

function NotFound() {
  return (
    <div className="max-w-xl mx-auto px-4 py-24 text-center">
      <p className="text-lg font-semibold text-brand-black">Page not found</p>
      <p className="text-sm text-brand-ink/70 mt-1">The page you&apos;re looking for doesn&apos;t exist.</p>
    </div>
  )
}
