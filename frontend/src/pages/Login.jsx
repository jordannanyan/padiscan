import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to={user.role === 'admin' ? '/admin' : '/'} replace />

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await login(form.email, form.password)
      navigate(u.role === 'admin' ? '/admin' : '/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-logo">🌾</div>
        <h1>PadiScan</h1>
        <p className="muted">Sistem Deteksi dan Klasifikasi Penyakit Daun Padi berbasis MobileNetV2</p>
        {error && <div className="alert error">{error}</div>}
        <label>Email</label>
        <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <label>Password</label>
        <input type="password" required value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="btn primary block" disabled={loading}>{loading ? 'Memproses...' : 'Login'}</button>
        <p className="muted center">Belum punya akun? <Link to="/register">Daftar di sini</Link></p>
      </form>
    </div>
  )
}
