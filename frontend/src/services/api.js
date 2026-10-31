/**
 * Centralized API client. Every request in the app goes through here.
 * The frontend only ever talks to FastAPI (this file) - never directly
 * to Ollama or PostgreSQL, per the architecture requirement.
 *
 * In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js),
 * so this stays a relative path with no hardcoded host and no secrets.
 */
const API_BASE = '/api/v1'

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function parseErrorDetail(response) {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    return JSON.stringify(body.detail)
  } catch {
    return response.statusText || 'Request failed'
  }
}

async function request(path, { method = 'GET', body, params, isFormData = false } = {}) {
  let url = `${API_BASE}${path}`
  if (params) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.set(key, value)
      }
    })
    const qs = query.toString()
    if (qs) url += `?${qs}`
  }

  const options = { method, headers: {} }
  if (body !== undefined) {
    if (isFormData) {
      options.body = body // FormData sets its own Content-Type/boundary
    } else {
      options.headers['Content-Type'] = 'application/json'
      options.body = JSON.stringify(body)
    }
  }

  let response
  try {
    response = await fetch(url, options)
  } catch (networkErr) {
    throw new ApiError(
      'Could not reach the server. Check that the backend is running and try again.',
      0,
      networkErr.message,
    )
  }

  if (!response.ok) {
    const detail = await parseErrorDetail(response)
    throw new ApiError(detail, response.status, detail)
  }

  if (response.status === 204) return null
  return response.json()
}

export const apiClient = {
  get: (path, params) => request(path, { method: 'GET', params }),
  post: (path, body, params) => request(path, { method: 'POST', body: body ?? {}, params }),
  postForm: (path, formData) => request(path, { method: 'POST', body: formData, isFormData: true }),
  delete: (path, params) => request(path, { method: 'DELETE', params }),
}
