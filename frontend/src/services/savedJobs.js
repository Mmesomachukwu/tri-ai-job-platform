import { apiClient } from './api'

// Maps to app/api/jobs.py:saved_router. Save/unsave only - no application
// status of any kind, per product requirements.

export function saveJob(jobId) {
  return apiClient.post(`/saved-jobs/${jobId}`)
}

export function unsaveJob(jobId) {
  return apiClient.delete(`/saved-jobs/${jobId}`)
}

export function getSavedJobs() {
  return apiClient.get('/saved-jobs')
}
