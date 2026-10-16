import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Beranda from './pages/Beranda'
import Deteksi from './pages/Deteksi'
import Riwayat from './pages/Riwayat'
import RiwayatDetail from './pages/RiwayatDetail'
import InfoPenyakit from './pages/InfoPenyakit'
import Profil from './pages/Profil'
import AdminDashboard from './pages/admin/Dashboard'
import KelolaPengguna from './pages/admin/KelolaPengguna'
import KelolaPenyakit from './pages/admin/KelolaPenyakit'
import LogDeteksi from './pages/admin/LogDeteksi'
import KelolaModel from './pages/admin/KelolaModel'

function Protected({ role, children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="center-page">Memuat...</div>
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) return <Navigate to="/" replace />
  return <Layout>{children}</Layout>
}

function Home() {
  const { user } = useAuth()
  return user?.role === 'admin' ? <Navigate to="/admin" replace /> : <Beranda />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route path="/" element={<Protected><Home /></Protected>} />
      <Route path="/deteksi" element={<Protected><Deteksi /></Protected>} />
      <Route path="/riwayat" element={<Protected><Riwayat /></Protected>} />
      <Route path="/riwayat/:id" element={<Protected><RiwayatDetail /></Protected>} />
      <Route path="/penyakit" element={<Protected><InfoPenyakit /></Protected>} />
      <Route path="/profil" element={<Protected><Profil /></Protected>} />

      <Route path="/admin" element={<Protected role="admin"><AdminDashboard /></Protected>} />
      <Route path="/admin/pengguna" element={<Protected role="admin"><KelolaPengguna /></Protected>} />
      <Route path="/admin/penyakit" element={<Protected role="admin"><KelolaPenyakit /></Protected>} />
      <Route path="/admin/log" element={<Protected role="admin"><LogDeteksi /></Protected>} />
      <Route path="/admin/model" element={<Protected role="admin"><KelolaModel /></Protected>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
