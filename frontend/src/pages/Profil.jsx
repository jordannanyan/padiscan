import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../AuthContext'

export default function Profil() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState({ nama: user.nama, password: '' })
  const [msg, setMsg] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    try {
      const d = await api('/auth/profil', { method: 'PUT', body: form })
      setUser({ ...user, nama: form.nama })
      setForm({ ...form, password: '' })
      setMsg({ type: 'success', text: d.message })
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    }
  }

  return (
    <>
      <h1>Profil</h1>
      <form className="card form-narrow" onSubmit={submit}>
        {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}
        <label>Email</label>
        <input value={user.email} disabled />
        <label>Nama</label>
        <input required value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} />
        <label>Password baru (kosongkan jika tidak diubah)</label>
        <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="btn primary">Simpan</button>
      </form>
    </>
  )
}
