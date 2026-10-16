import { percent } from '../api'

// Menampilkan hasil deteksi & klasifikasi: citra, nama penyakit, confidence score, probabilitas tiap kelas
export default function HasilKlasifikasi({ hasil }) {
  const probs = Object.entries(hasil.probabilitas || {}).sort((a, b) => b[1] - a[1])
  const label = (kode) => hasil.nama_kelas?.[kode] || kode

  return (
    <div className="hasil">
      <div className="card hasil-utama">
        <img src={hasil.url_citra} alt={hasil.nama_file} className="hasil-img" />
        <div>
          <div className="muted">Hasil Klasifikasi</div>
          <h2 className="hasil-nama">{hasil.nama_penyakit}</h2>
          <div className="muted"><em>{hasil.nama_latin}</em></div>
          <div className="confidence">
            <span>Confidence score</span>
            <strong>{percent(hasil.confidence_score)}</strong>
          </div>
          <div className="bar"><div style={{ width: `${hasil.confidence_score}%` }} /></div>
          <table className="meta">
            <tbody>
              <tr><td>File</td><td>{hasil.nama_file} ({hasil.ukuran_kb} KB)</td></tr>
              <tr><td>Tanggal deteksi</td><td>{hasil.tanggal_deteksi}</td></tr>
              {hasil.nama_model && <tr><td>Model</td><td>{hasil.nama_model} v{hasil.versi_model}</td></tr>}
              {hasil.waktu_proses_ms && <tr><td>Waktu proses</td><td>{hasil.waktu_proses_ms} ms</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3>Probabilitas Setiap Kelas</h3>
        {probs.map(([kode, p]) => (
          <div key={kode} className="prob-row">
            <span>{label(kode)}</span>
            <div className="bar small"><div style={{ width: `${p}%` }} /></div>
            <span className="prob-val">{percent(p)}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Informasi Penyakit</h3>
        <h4>Deskripsi</h4>
        <p>{hasil.deskripsi}</p>
        <h4>Gejala</h4>
        <p>{hasil.gejala}</p>
        <h4>Penanganan</h4>
        <p>{hasil.penanganan}</p>
      </div>
    </div>
  )
}
