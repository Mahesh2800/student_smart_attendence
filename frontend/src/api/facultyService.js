import api from './axiosConfig'
export const getFaculty = (params) => api.get('/attendance/faculty/', { params })
export const getMappings = () => api.get('/attendance/subject-mappings/')
