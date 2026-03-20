import { useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { toast } from 'react-toastify'

export default function Sidebar({ darkMode, setDarkMode }) {
  const navigate  = useNavigate()
  const location  = useLocation()
  const [user] = useState(() => JSON.parse(localStorage.getItem('user') || '{}'))

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    toast.success('Logged out successfully!')
    navigate('/login')
  }

  const navItems = [
    { icon: '📊', label: 'Dashboard',   path: '/dashboard'  },
    { icon: '🎮', label: 'Simulation',  path: '/simulation' },
    ...(user.is_admin ? [{ icon: '👑', label: 'Admin Panel', path: '/admin' }] : []),
  ]

  const initials = user.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0,2)
    : 'U'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>Business<br/><span>Intelligence</span></h1>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => (
          <div
            key={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}

        <div className="nav-item" onClick={() => setDarkMode(!darkMode)}>
          <span className="nav-icon">{darkMode ? '☀️' : '🌙'}</span>
          <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">{initials}</div>
          <div>
            <div className="user-name">{user.name || 'User'}</div>
            <div className="user-role">{user.is_admin ? '👑 Admin' : 'User'}</div>
          </div>
        </div>
        <button className="btn btn-danger btn-sm" style={{width:'100%'}} onClick={logout}>
          🚪 Logout
        </button>
      </div>
    </aside>
  )
}
