const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const TOKEN_KEY = 'goodplate_session_token'

export function getStoredToken() {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function storeToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY)
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getStoredToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}))
    throw new Error(problem.detail || `Request failed (${response.status})`)
  }
  if (response.status === 204) return null
  return response
}

async function jsonRequest(path, options) {
  return (await request(path, options)).json()
}

export const api = {
  register: (values) => jsonRequest('/auth/register', { method: 'POST', body: JSON.stringify(values) }),
  login: (values) => jsonRequest('/auth/login', { method: 'POST', body: JSON.stringify(values) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  profile: () => jsonRequest('/profile'),
  saveProfile: (profile) => jsonRequest('/profile', { method: 'PUT', body: JSON.stringify(profile) }),
  plans: () => jsonRequest('/plans'),
  generatePlan: () => jsonRequest('/plans', { method: 'POST' }),
  deletePlan: (id) => request(`/plans/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  files: () => jsonRequest('/files'),
  uploadFile: async (file) => {
    const body = new FormData()
    body.append('file', file)
    return jsonRequest('/files', { method: 'POST', body })
  },
  deleteFile: (id) => request(`/files/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  downloadFile: async (id) => (await request(`/files/${encodeURIComponent(id)}/download`)).blob(),
}
