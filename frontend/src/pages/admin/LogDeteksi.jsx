import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, percent } from '../../api'

export default function LogDeteksi() {
  const [rows, setRows] = useState([])
  const [q, setQ] = useState('')

  useEffect(() => { api('/admin/logs').then(setRows).catch(() => {}) }, [])

  const data = rows.filter((r) =>
    [r.nama_pengguna, r.email, r.nama_penyakit, r.nama_file].join(' ').toLowerCase().includes(q.toLowerCase()))

  return (
    <>
      <h1>Log Deteksi</h1>
      <div className="card">
        <div className="row between">
          <span className="muted">{data.length} dari {rows.length} deteksi</span>
          <input placeholder="Cari pengguna / penyakit / file..." value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr><th>No</th><th>Citra</th><th>Pengguna</th><th>File</th><th>Hasil</th><th>Confidence</th><th>Model</th><th>Tanggal</th></tr>
            </thead>
            <tbody>
              {data.map((r, i) => (
                <tr key={r.id_hasil}>
                  <td>{i + 1}</td>
                  <td><img src={r.url_citra} alt="" className="thumb" /></td>
                  <td>{r.nama_pengguna}<br /><small className="muted">{r.email}</small></td>
                  <td>{r.nama_file}</td>
                  <td><Link to={`/riwayat/${r.id_hasil}`}>{r.nama_penyakit}</Link></td>
                  <td>{percent(r.confidence_score)}</td>
                  <td>{r.nama_model ? `v${r.versi_model}` : '-'}</td>
                  <td>{r.tanggal_deteksi}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
