import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const MENU_PENGGUNA = [
  { to: '/', label: 'Beranda', icon: '🏠' },
  { to: '/deteksi', label: 'Deteksi Penyakit', icon: '🔍' },
  { to: '/riwayat', label: 'Riwayat Deteksi', icon: '🕘' },
  { to: '/penyakit', label: 'Informasi Penyakit', icon: '📖' },
  { to: '/profil', label: 'Profil', icon: '👤' },
]

const MENU_ADMIN = [
  { to: '/admin', label: 'Dashboard', icon: '📊' },
  { to: '/admin/pengguna', label: 'Kelola Pengguna', icon: '👥' },
  { to: '/admin/penyakit', label: 'Kelola Penyakit', icon: '🦠' },
  { to: '/admin/log', label: 'Log Deteksi', icon: '📋' },
  { to: '/admin/model', label: 'Kelola Model CNN', icon: '🧠' },
  { to: '/deteksi', label: 'Uji Deteksi', icon: '🔍' },
  { to: '/profil', label: 'Profil', icon: '👤' },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const menu = user.role === 'admin' ? MENU_ADMIN : MENU_PENGGUNA

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="brand">🌾 PadiScan</div>
        <div className="brand-sub">Deteksi Penyakit Daun Padi</div>
        <nav>
          {menu.map((m) => (
            <NavLink key={m.to} to={m.to} end={m.to === '/' || m.to === '/admin'} onClick={() => setOpen(false)}>
              <span>{m.icon}</span> {m.label}
            </NavLink>
          ))}
        </nav>
        <button className="btn-logout" onClick={handleLogout}>⏻ Logout</button>
      </aside>
      <div className="main">
        <header className="topbar">
          <button className="hamburger" onClick={() => setOpen(!open)}>☰</button>
          <div className="topbar-user">
            <strong>{user.nama}</strong>
            <span className={`badge ${user.role === 'admin' ? 'badge-dark' : ''}`}>
              {user.role === 'admin' ? 'Administrator' : 'Petani / Penyuluh'}
            </span>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  )
}
