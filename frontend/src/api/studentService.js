import api from './axiosConfig'
export const getStudents = (params) => api.get('/attendance/students/', { params })
export const getStudentPercentage = (id) => api.get(`/attendance/reports/student-percentage/${id}/`)
export const getLowAttendance = (threshold = 75) => api.get('/attendance/reports/low-attendance/', { params: { threshold } })
