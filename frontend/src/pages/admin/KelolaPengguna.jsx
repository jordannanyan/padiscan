import { useEffect, useState } from 'react'
import { api } from '../../api'
import { useAuth } from '../../AuthContext'

const EMPTY = { nama: '', email: '', password: '', role: 'pengguna' }

export default function KelolaPengguna() {
  const { user: me } = useAuth()
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(null)   // null = tertutup, objek = tambah / edit
  const [msg, setMsg] = useState(null)

  const load = () => api('/admin/users').then(setRows)
  useEffect(() => { load() }, [])

  const run = async (fn) => {
    try {
      const d = await fn()
      setMsg({ type: 'success', text: d.message })
      setForm(null)
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    }
  }

  const simpan = (e) => {
    e.preventDefault()
    run(() => form.id_pengguna
      ? api(`/admin/users/${form.id_pengguna}`, { method: 'PUT', body: form })
      : api('/admin/users', { method: 'POST', body: form }))
  }

  const toggleAktif = (u) =>
    run(() => api(`/admin/users/${u.id_pengguna}`, { method: 'PUT', body: { status_aktif: u.status_aktif ? 0 : 1 } }))

  return (
    <>
      <div className="row between">
        <h1>Kelola Data Pengguna</h1>
        <button className="btn primary" onClick={() => setForm(EMPTY)}>+ Tambah Pengguna</button>
      </div>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {form && (
        <form className="card form-narrow" onSubmit={simpan}>
          <h3>{form.id_pengguna ? 'Edit Pengguna' : 'Tambah Pengguna'}</h3>
          <label>Nama</label>
          <input required value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} />
          <label>Email</label>
          <input type="email" required disabled={!!form.id_pengguna} value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <label>Password {form.id_pengguna && '(kosongkan jika tidak diubah)'}</label>
          <input type="password" required={!form.id_pengguna} value={form.password || ''}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <label>Role</label>
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            <option value="pengguna">Pengguna (Petani/Penyuluh)</option>
            <option value="admin">Administrator</option>
          </select>
          <div className="row">
            <button className="btn primary">Simpan</button>
            <button type="button" className="btn" onClick={() => setForm(null)}>Batal</button>
          </div>
        </form>
      )}

      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr><th>No</th><th>Nama</th><th>Email</th><th>Role</th><th>Tgl Daftar</th><th>Jml Deteksi</th><th>Status</th><th>Aksi</th></tr>
          </thead>
          <tbody>
            {rows.map((u, i) => (
              <tr key={u.id_pengguna}>
                <td>{i + 1}</td>
                <td>{u.nama}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{u.tanggal_daftar}</td>
                <td>{u.jumlah_deteksi}</td>
                <td><span className={`chip ${u.status_aktif ? 'ok' : 'off'}`}>{u.status_aktif ? 'Aktif' : 'Nonaktif'}</span></td>
                <td className="nowrap">
                  <button className="btn small" onClick={() => setForm({ ...u, password: '' })}>Edit</button>{' '}
                  {u.id_pengguna !== me.id_pengguna && (
                    <button className={`btn small ${u.status_aktif ? 'danger' : ''}`} onClick={() => toggleAktif(u)}>
                      {u.status_aktif ? 'Nonaktifkan' : 'Aktifkan'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
