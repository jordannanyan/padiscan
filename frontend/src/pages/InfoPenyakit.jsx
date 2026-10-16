import { useEffect, useState } from 'react'
import { api } from '../api'

export default function InfoPenyakit() {
  const [rows, setRows] = useState([])
  const [aktif, setAktif] = useState(0)

  useEffect(() => { api('/penyakit').then(setRows).catch(() => {}) }, [])
  const p = rows[aktif]

  return (
    <>
      <h1>Informasi Penyakit Daun Padi</h1>
      <div className="tabs">
        {rows.map((r, i) => (
          <button key={r.id_penyakit} className={i === aktif ? 'active' : ''} onClick={() => setAktif(i)}>{r.nama}</button>
        ))}
      </div>
      {p && (
        <div className="card">
          <h2>{p.nama}</h2>
          <p className="muted">Penyebab: <em>{p.nama_latin}</em></p>
          <h4>Deskripsi</h4>
          <p>{p.deskripsi}</p>
          <h4>Gejala</h4>
          <p>{p.gejala}</p>
          <h4>Penanganan</h4>
          <p>{p.penanganan}</p>
        </div>
      )}
    </>
  )
}
