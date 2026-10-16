import { useEffect, useState } from 'react'
import { api } from '../../api'

export default function KelolaPenyakit() {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(null)
  const [msg, setMsg] = useState(null)

  const load = () => api('/penyakit').then(setRows)
  useEffect(() => { load() }, [])

  const simpan = async (e) => {
    e.preventDefault()
    try {
      const d = await api(`/penyakit/${form.id_penyakit}`, { method: 'PUT', body: form })
      setMsg({ type: 'success', text: d.message })
      setForm(null)
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    }
  }

  const area = (name, label) => (
    <>
      <label>{label}</label>
      <textarea rows={3} value={form[name] || ''} onChange={(e) => setForm({ ...form, [name]: e.target.value })} />
    </>
  )

  return (
    <>
      <h1>Kelola Data Penyakit</h1>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {form && (
        <form className="card" onSubmit={simpan}>
          <h3>Edit: {form.nama}</h3>
          <label>Kode kelas model</label>
          <input value={form.kode_kelas} disabled />
          <label>Nama Penyakit</label>
          <input required value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} />
          <label>Nama Latin / Penyebab</label>
          <input value={form.nama_latin || ''} onChange={(e) => setForm({ ...form, nama_latin: e.target.value })} />
          {area('deskripsi', 'Deskripsi')}
          {area('gejala', 'Gejala')}
          {area('penanganan', 'Penanganan')}
          <div className="row">
            <button className="btn primary">Simpan</button>
            <button type="button" className="btn" onClick={() => setForm(null)}>Batal</button>
          </div>
        </form>
      )}

      <div className="card table-wrap">
        <table className="table">
          <thead><tr><th>No</th><th>Kode Kelas</th><th>Nama</th><th>Penyebab</th><th>Gejala</th><th>Aksi</th></tr></thead>
          <tbody>
            {rows.map((p, i) => (
              <tr key={p.id_penyakit}>
                <td>{i + 1}</td>
                <td><code>{p.kode_kelas}</code></td>
                <td>{p.nama}</td>
                <td><em>{p.nama_latin}</em></td>
                <td className="clip">{p.gejala}</td>
                <td><button className="btn small" onClick={() => setForm(p)}>Edit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
