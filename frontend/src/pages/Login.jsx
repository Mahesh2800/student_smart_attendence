import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { user, login, logout } = useAuth()
  const navigate = useNavigate()
  const [role, setRole] = useState('faculty')
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to={`/${user.role}`} replace />
  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const session = await login(form.username.trim(), form.password)
      if (session.role !== role) {
        logout()
        setError(`This account is a ${session.role} account. Choose the ${session.role} login to continue.`)
        return
      }
      navigate(`/${session.role}`)
    } catch {
      setError('Invalid credentials. Check your username and password.')
    } finally {
      setBusy(false)
    }
  }
  const accountLabel = role === 'faculty' ? 'Faculty' : role === 'student' ? 'Student' : 'Admin'
  const placeholder = role === 'faculty' ? 'e.g. faculty1' : role === 'student' ? 'e.g. student1' : 'e.g. admin'
  return <main className="login-page"><section className="login-aside"><div className="brand inverse"><span className="brand-mark">A</span><span>Attendly</span></div><div className="login-message"><span className="eyebrow">COLLEGE OPERATIONS</span><h1>Every class, accounted for.</h1><p>One calm workspace for marking, reviewing, and acting on attendance.</p></div><div className="login-stat"><strong>5,000+</strong><span>students ready to be seen</span></div></section><section className="login-panel"><div className="form-wrap"><span className="eyebrow">WELCOME BACK</span><h2>Sign in to your workspace</h2><p className="muted">Choose your account type to enter the right workspace.</p><div className="login-role-switch">{[['faculty', 'Faculty'], ['student', 'Student'], ['admin', 'Admin']].map(([value, label]) => <button type="button" key={value} className={role === value ? 'login-role-button active' : 'login-role-button'} onClick={() => { setRole(value); setError('') }}>{label}</button>)}</div><form onSubmit={submit}><label>{accountLabel} username<input required value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} placeholder={placeholder} /></label><label>Password<input required type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder="Enter password" /></label>{error && <div className="form-error">{error}</div>}<button className="button primary full" disabled={busy}>{busy ? 'Signing in...' : `Continue as ${role}`}</button></form><p className="demo-note">Demo: faculty1 / Faculty@123 · student1 / Student@123 · admin / Admin@123</p></div></section></main>
}
