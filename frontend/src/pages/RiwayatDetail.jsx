import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import HasilKlasifikasi from '../components/HasilKlasifikasi'

export default function RiwayatDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [hasil, setHasil] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api(`/history/${id}`).then(setHasil).catch((e) => setError(e.message))
  }, [id])

  return (
    <>
      <button className="btn" onClick={() => navigate(-1)}>← Kembali</button>
      <h1>Detail Hasil Deteksi</h1>
      {error && <div className="alert error">{error}</div>}
      {hasil ? <HasilKlasifikasi hasil={hasil} /> : !error && <p>Memuat...</p>}
    </>
  )
}
