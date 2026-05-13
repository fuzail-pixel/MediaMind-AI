import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

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

export const listDocuments = () => api.get('/documents')

export const getDocument = (id) => api.get(`/documents/${id}`)

export const deleteDocument = (id) => api.delete(`/documents/${id}`)

// Search
export const searchDocuments = (query) =>
  api.get('/search', { params: { q: query } })

// Chat
export const askQuestion = (payload) => api.post('/chat/ask', payload)

export const summarizeDocument = (document_id) =>
  api.post('/chat/summarize', { document_id })

export const getChatHistory = (document_id) =>
  api.get(`/chat/sessions/${document_id}`)

// Health
export const healthCheck = () =>
  axios.get('http://localhost:8000/health')

export default api
