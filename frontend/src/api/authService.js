import api, { setTokens, clearTokens } from './axiosConfig'
export async function loginRequest(username, password) { const { data } = await api.post('/auth/login/', { username, password }); setTokens(data.access, data.refresh); return data }
export function logoutRequest() { clearTokens() }
