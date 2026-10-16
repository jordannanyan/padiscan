import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, percent } from '../api'

export default function Riwayat() {
  const [rows, setRows] = useState(null)
  const [filter, setFilter] = useState('')

  const load = () => api('/history').then(setRows).catch(() => setRows([]))
  useEffect(() => { load() }, [])

  const hapus = async (id) => {
    if (!confirm('Hapus riwayat deteksi ini?')) return
    await api(`/history/${id}`, { method: 'DELETE' })
    load()
  }

  if (rows === null) return <p>Memuat...</p>
  const penyakit = [...new Set(rows.map((r) => r.nama_penyakit))]
  const data = filter ? rows.filter((r) => r.nama_penyakit === filter) : rows

  return (
    <>
      <h1>Riwayat Deteksi</h1>
      {rows.length === 0 ? (
        <div className="card"><p className="muted">Belum ada riwayat deteksi. <Link to="/deteksi">Mulai deteksi</Link></p></div>
      ) : (
        <div className="card">
          <div className="row between">
            <span className="muted">{data.length} data, diurutkan dari yang terbaru</span>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">Semua penyakit</option>
              {penyakit.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>No</th><th>Citra</th><th>Nama File</th><th>Hasil Klasifikasi</th><th>Confidence</th><th>Tanggal</th><th>Aksi</th></tr>
              </thead>
              <tbody>
                {data.map((r, i) => (
                  <tr key={r.id_hasil}>
                    <td>{i + 1}</td>
                    <td><img src={r.url_citra} alt="" className="thumb" /></td>
                    <td>{r.nama_file}</td>
                    <td><span className="chip">{r.nama_penyakit}</span></td>
                    <td>{percent(r.confidence_score)}</td>
                    <td>{r.tanggal_deteksi}</td>
                    <td className="nowrap">
                      <Link className="btn small" to={`/riwayat/${r.id_hasil}`}>Detail</Link>{' '}
                      <button className="btn small danger" onClick={() => hapus(r.id_hasil)}>Hapus</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
