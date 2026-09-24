import api from './axiosConfig'
export const getSessions = (params) => api.get('/attendance/sessions/', { params })
export const getRecords = (params) => api.get('/attendance/records/', { params })
export const markBulk = (id, records) => api.post(`/attendance/sessions/${id}/mark-bulk/`, { records })
export const getCorrections = () => api.get('/attendance/corrections/')
export const createCorrection = (payload) => api.post('/attendance/corrections/', payload)
export const resolveCorrection = (id, action) => api.post(`/attendance/corrections/${id}/${action}/`)
