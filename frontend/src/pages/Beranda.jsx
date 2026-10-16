import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, percent } from '../api'
import { useAuth } from '../AuthContext'

export default function Beranda() {
  const { user } = useAuth()
  const [riwayat, setRiwayat] = useState([])

  useEffect(() => {
    api('/history').then(setRiwayat).catch(() => {})
  }, [])

  const perPenyakit = riwayat.reduce((acc, r) => ({ ...acc, [r.nama_penyakit]: (acc[r.nama_penyakit] || 0) + 1 }), {})

  return (
    <>
      <h1>Selamat datang, {user.nama} 👋</h1>
      <p className="muted">Unggah foto daun padi untuk mendeteksi penyakit Bacterial Blight, Blast, Brown Spot, atau Tungro.</p>

      <div className="grid-3">
        <Link to="/deteksi" className="card action-card">
          <div className="action-icon">🔍</div>
          <strong>Deteksi Penyakit</strong>
          <span className="muted">Unggah citra daun padi</span>
        </Link>
        <Link to="/riwayat" className="card action-card">
          <div className="action-icon">🕘</div>
          <strong>{riwayat.length} Riwayat</strong>
          <span className="muted">Lihat hasil deteksi sebelumnya</span>
        </Link>
        <Link to="/penyakit" className="card action-card">
          <div className="action-icon">📖</div>
          <strong>Informasi Penyakit</strong>
          <span className="muted">Gejala dan penanganan</span>
        </Link>
      </div>

      {Object.keys(perPenyakit).length > 0 && (
        <div className="card">
          <h3>Ringkasan Deteksi Anda</h3>
          <div className="chips">
            {Object.entries(perPenyakit).map(([nama, n]) => <span key={nama} className="chip">{nama}: <b>{n}</b></span>)}
          </div>
        </div>
      )}

      <div className="card">
        <h3>Deteksi Terakhir</h3>
        {riwayat.length === 0 ? (
          <p className="muted">Belum ada riwayat deteksi.</p>
        ) : (
          <table className="table">
            <thead><tr><th>Citra</th><th>Penyakit</th><th>Confidence</th><th>Tanggal</th></tr></thead>
            <tbody>
              {riwayat.slice(0, 5).map((r) => (
                <tr key={r.id_hasil}>
                  <td><img src={r.url_citra} alt="" className="thumb" /></td>
                  <td><Link to={`/riwayat/${r.id_hasil}`}>{r.nama_penyakit}</Link></td>
                  <td>{percent(r.confidence_score)}</td>
                  <td>{r.tanggal_deteksi}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
