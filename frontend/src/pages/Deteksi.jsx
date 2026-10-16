import { useRef, useState } from 'react'
import { api } from '../api'
import HasilKlasifikasi from '../components/HasilKlasifikasi'

const MAX_MB = 5
const ALLOWED = ['image/jpeg', 'image/png']

export default function Deteksi() {
  const inputRef = useRef()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [hasil, setHasil] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [drag, setDrag] = useState(false)

  const pilihFile = (f) => {
    setError('')
    setHasil(null)
    if (!f) return
    if (!ALLOWED.includes(f.type)) return setError('Format file harus JPG atau PNG')
    if (f.size > MAX_MB * 1024 * 1024) return setError(`Ukuran file maksimal ${MAX_MB} MB`)
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const deteksi = async () => {
    if (!file) return setError('Pilih citra daun padi terlebih dahulu')
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('citra', file)
      setHasil(await api('/detect', { method: 'POST', form }))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setPreview(null)
    setHasil(null)
    setError('')
    inputRef.current.value = ''
  }

  return (
    <>
      <h1>Deteksi & Klasifikasi Penyakit</h1>
      <p className="muted">Unggah foto daun padi (JPG/PNG, maks. {MAX_MB} MB). Citra akan diubah ke 224×224 piksel lalu
        diproses oleh model MobileNetV2.</p>

      <div className="card">
        <div
          className={`dropzone ${drag ? 'drag' : ''}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pilihFile(e.dataTransfer.files[0]) }}
        >
          {preview ? (
            <img src={preview} alt="preview" className="preview" />
          ) : (
            <>
              <div className="action-icon">📷</div>
              <strong>Klik atau seret citra daun padi ke sini</strong>
              <span className="muted">Format JPG / PNG</span>
            </>
          )}
        </div>
        <input ref={inputRef} type="file" accept="image/jpeg,image/png" hidden
          onChange={(e) => pilihFile(e.target.files[0])} />
        {file && <p className="muted">{file.name} — {(file.size / 1024).toFixed(1)} KB</p>}
        {error && <div className="alert error">{error}</div>}
        <div className="row">
          <button className="btn primary" onClick={deteksi} disabled={loading || !file}>
            {loading ? '⏳ Mendeteksi...' : '🔍 Deteksi Sekarang'}
          </button>
          {file && <button className="btn" onClick={reset} disabled={loading}>Ganti Citra</button>}
        </div>
      </div>

      {hasil && <HasilKlasifikasi hasil={hasil} />}
    </>
  )
}
