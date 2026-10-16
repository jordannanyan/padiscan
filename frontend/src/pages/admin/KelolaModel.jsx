import { useEffect, useState } from 'react'
import { api, percent } from '../../api'

const EMPTY = { nama: 'MobileNetV2 Penyakit Daun Padi', arsitektur: 'MobileNetV2', versi: '', akurasi: '', tanggal_pelatihan: '' }

export default function KelolaModel() {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(null)
  const [file, setFile] = useState(null)
  const [msg, setMsg] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = () => api('/admin/models').then(setRows)
  useEffect(() => { load() }, [])

  const run = async (fn) => {
    setLoading(true)
    try {
      const d = await fn()
      setMsg({ type: 'success', text: d.message })
      setForm(null)
      setFile(null)
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  const simpan = (e) => {
    e.preventDefault()
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => fd.append(k, v))
    if (file) fd.append('file', file)
    run(() => api('/admin/models', { method: 'POST', form: fd }))
  }

  return (
    <>
      <div className="row between">
        <h1>Kelola Model CNN</h1>
        <button className="btn primary" onClick={() => setForm(EMPTY)}>+ Tambah Versi Model</button>
      </div>
      <p className="muted">Unggah file model hasil training (.keras / .h5), atau isi nama file yang sudah ada di folder
        <code> backend/models</code>. Hanya satu model yang aktif dan dipakai untuk deteksi.</p>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {form && (
        <form className="card form-narrow" onSubmit={simpan}>
          <h3>Tambah Versi Model</h3>
          <label>Nama Model</label>
          <input required value={form.nama} onChange={(e) => setForm({ ...form, nama: e.target.value })} />
          <label>Arsitektur</label>
          <input required value={form.arsitektur} onChange={(e) => setForm({ ...form, arsitektur: e.target.value })} />
          <label>Versi</label>
          <input required placeholder="mis. 1.1" value={form.versi} onChange={(e) => setForm({ ...form, versi: e.target.value })} />
          <label>Akurasi data uji (0 - 1)</label>
          <input type="number" step="0.0001" min="0" max="1" value={form.akurasi}
            onChange={(e) => setForm({ ...form, akurasi: e.target.value })} />
          <label>Tanggal Pelatihan</label>
          <input type="date" value={form.tanggal_pelatihan}
            onChange={(e) => setForm({ ...form, tanggal_pelatihan: e.target.value })} />
          <label>File Model (.keras / .h5)</label>
          <input type="file" accept=".keras,.h5" onChange={(e) => setFile(e.target.files[0])} />
          {!file && (
            <>
              <label>atau nama file di folder backend/models</label>
              <input placeholder="mobilenetv2_padi.keras" value={form.path_file || ''}
                onChange={(e) => setForm({ ...form, path_file: e.target.value })} />
            </>
          )}
          <div className="row">
            <button className="btn primary" disabled={loading}>{loading ? 'Mengunggah...' : 'Simpan'}</button>
            <button type="button" className="btn" onClick={() => setForm(null)}>Batal</button>
          </div>
        </form>
      )}

      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr><th>Nama</th><th>Arsitektur</th><th>Versi</th><th>Akurasi</th><th>File</th><th>Tgl Pelatihan</th><th>Status</th><th>Aksi</th></tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr key={m.id_model}>
                <td>{m.nama}</td>
                <td>{m.arsitektur}</td>
                <td>{m.versi}</td>
                <td>{m.akurasi != null ? percent(m.akurasi * 100) : '-'}</td>
                <td><code>{m.path_file}</code>{!m.file_tersedia && <span className="chip off">file hilang</span>}</td>
                <td>{m.tanggal_pelatihan || '-'}</td>
                <td><span className={`chip ${m.aktif ? 'ok' : ''}`}>{m.aktif ? 'Aktif' : 'Tidak aktif'}</span></td>
                <td className="nowrap">
                  {!m.aktif && (
                    <>
                      <button className="btn small" onClick={() => run(() => api(`/admin/models/${m.id_model}/aktifkan`, { method: 'PUT' }))}>Aktifkan</button>{' '}
                      <button className="btn small danger" onClick={() => confirm('Hapus model ini?') && run(() => api(`/admin/models/${m.id_model}`, { method: 'DELETE' }))}>Hapus</button>
                    </>
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
