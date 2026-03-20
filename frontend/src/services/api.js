import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

// ── Create axios instance ─────────────────────────────────────────
const api = axios.create({ baseURL: BASE_URL })

// ── Auto-attach JWT token to every request ────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Auto-logout on 401 ────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────
export const register = (data) => api.post('/auth/register', data)
export const login    = (data) => api.post('/auth/login', data)
export const getMe    = ()     => api.get('/auth/me')

// ── Data ──────────────────────────────────────────────────────────
export const getBusinessData = ()           => api.get('/business-data')
export const getDataCount    = ()           => api.get('/data-count')
export const clearData       = ()           => api.delete('/clear-data')
export const downloadSampleCSV = ()         => `${BASE_URL}/sample-csv`

// ── Upload ────────────────────────────────────────────────────────
export const uploadCSV = (file, mode = 'replace') => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/upload?mode=${mode}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ── ML Features ───────────────────────────────────────────────────
export const getForecast  = (periods = 3) => api.get(`/forecast?periods=${periods}`)
export const getAnomaly   = ()            => api.get('/anomaly')
export const getHealth    = ()            => api.get('/health')
export const getTips      = ()            => api.get('/tips')
export const simulate     = (data)        => api.post('/simulate', data)

// ── AI & Reports ──────────────────────────────────────────────────
export const chat         = (message)     => api.post('/chat', { message })
export const sendEmail    = (to_email)    => api.post('/email/alert', { to_email })
export const downloadReport = ()          => `${BASE_URL}/report/download`

// ── Admin ─────────────────────────────────────────────────────────
export const getAdminOverview  = ()       => api.get('/admin/overview')
export const getAdminUsers     = ()       => api.get('/admin/users')
export const getUserData       = (id)     => api.get(`/admin/users/${id}/data`)
export const deleteUser        = (id)     => api.delete(`/admin/users/${id}`)

export default api