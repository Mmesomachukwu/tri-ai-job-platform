import { apiClient } from './api'

/**
 * Maps directly to app/api/jobs.py. Field names match app/schemas/job.py
 * (JobOut/JobListResponse) exactly - inspected from the live backend
 * before writing this file.
 */

export function searchJobs({
  keyword, category, location, remoteType, employmentType, experienceLevel,
  salaryMin, salaryMax, skills, page = 1, pageSize = 20,
} = {}) {
  return apiClient.get('/jobs', {
    keyword,
    category,
    location,
    remote_type: remoteType,
    employment_type: employmentType,
    experience_level: experienceLevel,
    salary_min: salaryMin,
    salary_max: salaryMax,
    skills, // comma-separated string, per backend contract
    page,
    page_size: pageSize,
  })
}

export function getJob(jobId) {
  return apiClient.get(`/jobs/${jobId}`)
}

/**
 * Pulls fresh real jobs from RealJobProvider into the DB. Throws ApiError
 * with status 503 if the real provider is unreachable - callers must
 * show the required "Unable to retrieve real jobs right now" message,
 * never substitute fake data.
 */
export function syncJobs(query) {
  return apiClient.post('/jobs/sync', undefined, { query })
}

// Categories mirror app/jobs/normalizer.py:CATEGORY_KEYWORDS - kept as a
// simple constant here since the backend doesn't expose a categories-list
// endpoint; this is a UI convenience only, not invented data (every value
// exactly matches what the backend's classify_category() actually
// produces and stores on real jobs).
export const JOB_CATEGORIES = [
  'Data Science & AI',
  'Software Engineering',
  'Cloud & DevOps',
  'Cybersecurity',
  'Data Infrastructure',
  'Other Technology',
]

export const REMOTE_TYPES = ['Remote', 'Hybrid', 'On-site']
export const EMPLOYMENT_TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship']
export const EXPERIENCE_LEVELS = ['Entry', 'Junior', 'Mid-level', 'Senior', 'Lead']

export const POPULAR_SEARCHES = [
  'Data Scientist', 'Software Engineer', 'ML Engineer', 'Data Engineer',
  'Cloud Engineer', 'DevOps Engineer', 'AI Engineer',
]
