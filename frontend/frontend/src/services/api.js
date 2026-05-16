import axios from 'axios'
import { authService } from './auth'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

// Add token to every request automatically
api.interceptors.request.use((config) => {
  const token = authService.getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 — redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      authService.removeToken()
      window.location.href = '/login'
    }
    const message =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

// Auth
export const getMe  = ()  => api.get('/auth/me')
export const logout = ()  => api.post('/auth/logout')

// Documents
export const uploadFile = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
}

export const listDocuments   = ()      => api.get('/documents')
export const getDocument     = (id)    => api.get(`/documents/${id}`)
export const deleteDocument  = (id)    => api.delete(`/documents/${id}`)
export const searchDocuments = (query) => api.get('/search', { params: { q: query } })

// Chat
export const askQuestion      = (payload)     => api.post('/chat/ask', payload)
export const summarizeDocument = (document_id) => api.post('/chat/summarize', { document_id })
export const getChatHistory   = (document_id) => api.get(`/chat/sessions/${document_id}`)

// Streaming — fetch needs token manually since it bypasses axios
export const streamAnswer = (document_id, question, session_id = null) => {
  const token = authService.getToken()
  return fetch(`${API_BASE}/chat/stream`, {
    method : 'POST',
    headers: {
      'Content-Type' : 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ document_id, question, session_id })
  })
}

// Health
export const healthCheck = () => axios.get('http://localhost:8000/health')

export default api