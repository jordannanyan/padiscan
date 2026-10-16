import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ nama: '', email: '', password: '', konfirmasi: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.konfirmasi) return setError('Konfirmasi password tidak sama')
    try {
      const d = await api('/auth/register', { method: 'POST', body: form })
      setSuccess(d.message)
      setTimeout(() => navigate('/login'), 1500)
    } catch (err) {
      setError(err.message)
    }
  }

  const field = (name, label, type = 'text') => (
    <>
      <label>{label}</label>
      <input type={type} required value={form[name]} onChange={(e) => setForm({ ...form, [name]: e.target.value })} />
    </>
  )

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-logo">🌾</div>
        <h1>Registrasi Akun</h1>
        <p className="muted">Untuk petani dan penyuluh pertanian</p>
        {error && <div className="alert error">{error}</div>}
        {success && <div className="alert success">{success}</div>}
        {field('nama', 'Nama Lengkap')}
        {field('email', 'Email', 'email')}
        {field('password', 'Password (min. 6 karakter)', 'password')}
        {field('konfirmasi', 'Konfirmasi Password', 'password')}
        <button className="btn primary block">Daftar</button>
        <p className="muted center">Sudah punya akun? <Link to="/login">Login</Link></p>
      </form>
    </div>
  )
}
