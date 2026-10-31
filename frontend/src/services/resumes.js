import { apiClient } from './api'

// Maps to app/api/resumes.py. Field names match app/schemas/resume.py
// (ResumeOut/ResumeVersionOut) exactly.

export const ALLOWED_EXTENSIONS = ['.pdf', '.docx']
export const MAX_FILE_SIZE_MB = 5

export function validateFileBeforeUpload(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `Unsupported file type "${ext}". Please upload a PDF or DOCX file.`
  }
  if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
    return `File exceeds the ${MAX_FILE_SIZE_MB}MB size limit.`
  }
  return null
}

export function uploadResume(file, label) {
  const formData = new FormData()
  formData.append('file', file)
  if (label) formData.append('label', label)
  return apiClient.postForm('/resumes/upload', formData)
}

export function listResumes() {
  return apiClient.get('/resumes')
}

export function getResume(resumeId) {
  return apiClient.get(`/resumes/${resumeId}`)
}

export function deleteResume(resumeId) {
  return apiClient.delete(`/resumes/${resumeId}`)
}

export function optimizeResume(resumeId, jobId) {
  return apiClient.post(`/resumes/${resumeId}/optimize/${jobId}`)
}

export function listResumeVersions(resumeId) {
  return apiClient.get(`/resumes/${resumeId}/versions`)
}
