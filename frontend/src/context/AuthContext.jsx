import { createContext, useContext, useState } from 'react'
import { loginRequest, logoutRequest } from '../api/authService'

const AuthContext = createContext(null)
const roleFromPayload = (payload) => payload.role || (payload.is_staff ? 'admin' : payload.username?.startsWith('faculty') ? 'faculty' : 'student')
export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const login = async (username, password) => { const payload = await loginRequest(username, password); const next = { ...payload, username, role: roleFromPayload(payload) }; setSession(next); return next }
  const logout = () => { logoutRequest(); setSession(null) }
  return <AuthContext.Provider value={{ user: session, role: session?.role, token: session?.access, login, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)
