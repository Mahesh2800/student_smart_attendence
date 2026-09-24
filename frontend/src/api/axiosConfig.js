import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1' })
let accessToken = null
let refreshToken = null
export const setTokens = (access, refresh) => { accessToken = access; refreshToken = refresh }
export const clearTokens = () => { accessToken = null; refreshToken = null }
api.interceptors.request.use((config) => { if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`; return config })
api.interceptors.response.use((response) => response, async (error) => {
  const original = error.config
  if (error.response?.status === 401 && refreshToken && !original._retry) {
    original._retry = true
    try { const response = await axios.post(`${api.defaults.baseURL}/auth/refresh/`, { refresh: refreshToken }); accessToken = response.data.access; original.headers.Authorization = `Bearer ${accessToken}`; return api(original) } catch { clearTokens() }
  }
  return Promise.reject(error)
})
export default api
