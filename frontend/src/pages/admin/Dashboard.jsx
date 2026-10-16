import { useEffect, useState } from 'react'
import { api, percent } from '../../api'

export default function Dashboard() {
  const [s, setS] = useState(null)

  useEffect(() => { api('/admin/stats').then(setS).catch(() => {}) }, [])
  if (!s) return <p>Memuat...</p>

  const maxPenyakit = Math.max(1, ...s.per_penyakit.map((p) => p.jumlah))
  const maxHari = Math.max(1, ...s.per_hari.map((p) => p.jumlah))

  return (
    <>
      <h1>Dashboard Administrator</h1>
      <div className="grid-4">
        <div className="card stat"><span>Total Pengguna</span><strong>{s.total.total_pengguna}</strong>
          <small className="muted">{s.total.pengguna_aktif} aktif</small></div>
        <div className="card stat"><span>Total Deteksi</span><strong>{s.total.total_deteksi}</strong></div>
        <div className="card stat"><span>Deteksi Hari Ini</span><strong>{s.total.deteksi_hari_ini}</strong></div>
        <div className="card stat"><span>Rata-rata Confidence</span>
          <strong>{s.total.rata_confidence != null ? percent(s.total.rata_confidence) : '-'}</strong></div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Jumlah Deteksi per Penyakit</h3>
          {s.per_penyakit.map((p) => (
            <div key={p.kode_kelas} className="prob-row">
              <span>{p.nama}</span>
              <div className="bar small"><div style={{ width: `${(p.jumlah / maxPenyakit) * 100}%` }} /></div>
              <span className="prob-val">{p.jumlah}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Deteksi 7 Hari Terakhir</h3>
          {s.per_hari.length === 0 ? <p className="muted">Belum ada data.</p> : (
            <div className="vchart">
              {s.per_hari.map((d) => (
                <div key={d.tanggal} className="vbar">
                  <span>{d.jumlah}</span>
                  <div style={{ height: `${(d.jumlah / maxHari) * 140}px` }} />
                  <small>{d.tanggal.slice(5)}</small>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Model CNN Aktif</h3>
        {s.model_aktif ? (
          <p>{s.model_aktif.nama} — versi {s.model_aktif.versi} — akurasi uji{' '}
            <b>{s.model_aktif.akurasi != null ? percent(s.model_aktif.akurasi * 100) : '-'}</b></p>
        ) : <div className="alert error">Belum ada model aktif. Daftarkan model di menu Kelola Model CNN.</div>}
      </div>
    </>
  )
}
