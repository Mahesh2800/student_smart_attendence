import api from './axiosConfig'
export const getClassSummary = (params) => api.get('/attendance/reports/class-summary/', { params })
export const exportCsv = (params) => api.get('/attendance/reports/export-csv/', { params, responseType: 'blob' })
