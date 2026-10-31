import { apiClient } from './api'

// Maps to app/api/analyses.py. Field names match app/schemas/analysis.py
// (AnalysisOut) exactly, inspected from a live response.

export function analyzeResume(resumeId, jobId) {
  return apiClient.post(`/analyses/resumes/${resumeId}/jobs/${jobId}`)
}

export function getAnalysis(resumeId, jobId) {
  return apiClient.get(`/analyses/resumes/${resumeId}/jobs/${jobId}`)
}

export function listAnalyses() {
  return apiClient.get('/analyses')
}

// Score components in display order, mapped to AnalysisOut field names -
// the ONLY numbers ever rendered come straight from the backend response.
export const SCORE_COMPONENTS = [
  { key: 'skills_score', label: 'Technical Skills' },
  { key: 'keyword_score', label: 'Keywords' },
  { key: 'experience_score', label: 'Experience' },
  { key: 'responsibility_score', label: 'Responsibilities' },
  { key: 'education_score', label: 'Education' },
  { key: 'structure_score', label: 'Resume Structure' },
  { key: 'semantic_score', label: 'Semantic Similarity' },
]
