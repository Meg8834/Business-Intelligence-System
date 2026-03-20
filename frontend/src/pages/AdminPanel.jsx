import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import Sidebar from '../components/Sidebar'
import { getAdminOverview, getAdminUsers, getUserData, deleteUser } from '../services/api'

export default function AdminPanel() {
  const [darkMode,   setDarkMode]   = useState(false)
  const [overview,   setOverview]   = useState(null)
  const [users,      setUsers]      = useState([])
  const [userData,   setUserData]   = useState(null)
  const [activeUser, setActiveUser] = useState(null)
  const [loading,    setLoading]    = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  useEffect(() => {
    fetchOverview()
  }, [])

  const fetchOverview = async () => {
    setLoading(true)
    try {
      const [ovRes, usersRes] = await Promise.all([
        getAdminOverview(),
        getAdminUsers(),
      ])
      setOverview(ovRes.data)
      setUsers(usersRes.data.users)
    } catch {
      toast.error('Failed to load admin data.')
    } finally {
      setLoading(false)
    }
  }

  const handleViewUser = async (user) => {
    setActiveUser(user)
    try {
      const res = await getUserData(user.id)
      setUserData(res.data)
    } catch {
      toast.error('Failed to load user data.')
    }
  }

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Delete ${user.email} and all their data?`)) return
    try {
      await deleteUser(user.id)
      toast.success(`User ${user.email} deleted.`)
      fetchOverview()
      if (activeUser?.id === user.id) { setActiveUser(null); setUserData(null) }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Delete failed.')
    }
  }

  const fmt = (n) => `₹${Number(n).toLocaleString('en-IN')}`

  return (
    <div className="app-layout">
      <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} />

      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">👑 Admin Panel</h1>
          <p className="page-subtitle">Manage all users and their business data</p>
        </div>

        {/* Overview metrics */}
        {overview && (
          <div className="metrics-grid" style={{marginBottom:'1.5rem'}}>
            <div className="metric-card">
              <div className="metric-label">Total Users</div>
              <div className="metric-value">{overview.total_users}</div>
            </div>
            <div className="metric-card success">
              <div className="metric-label">Total Records</div>
              <div className="metric-value">{overview.total_records}</div>
            </div>
            <div className="metric-card warning">
              <div className="metric-label">Active Users</div>
              <div className="metric-value">{overview.users?.filter(u => u.data_records > 0).length}</div>
            </div>
            <div className="metric-card accent">
              <div className="metric-label">Admins</div>
              <div className="metric-value">{overview.users?.filter(u => u.is_admin).length}</div>
            </div>
          </div>
        )}

        <div className="grid-2">
          {/* Users list */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">👥 All Users</h3>
              <span className="badge badge-primary">{users.length} users</span>
            </div>
            {loading ? (
              <div className="loading-overlay">
                <div className="loading-spinner"></div> Loading users...
              </div>
            ) : (
              <div style={{display:'flex', flexDirection:'column', gap:'0.75rem'}}>
                {users.map(user => (
                  <div
                    key={user.id}
                    style={{
                      padding:'0.875rem',
                      border:`1.5px solid ${activeUser?.id === user.id ? 'var(--primary)' : 'var(--border)'}`,
                      borderRadius:8,
                      cursor:'pointer',
                      background: activeUser?.id === user.id ? 'var(--primary-light)' : 'var(--bg)',
                      transition:'all 0.2s',
                    }}
                    onClick={() => handleViewUser(user)}
                  >
                    <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                      <div style={{display:'flex', alignItems:'center', gap:'0.75rem'}}>
                        <div style={{
                          width:36, height:36, borderRadius:'50%',
                          background:'var(--primary)', color:'#fff',
                          display:'flex', alignItems:'center', justifyContent:'center',
                          fontWeight:700, fontSize:'0.85rem',
                          fontFamily:'var(--font-display)',
                        }}>
                          {user.name?.slice(0,2).toUpperCase()}
                        </div>
                        <div>
                          <div style={{fontWeight:600, fontSize:'0.9rem'}}>
                            {user.name}
                            {user.is_admin && <span className="badge badge-primary" style={{marginLeft:6}}>Admin</span>}
                          </div>
                          <div style={{fontSize:'0.8rem', color:'var(--text-muted)'}}>{user.email}</div>
                        </div>
                      </div>
                      <div style={{display:'flex', alignItems:'center', gap:'0.5rem'}}>
                        <span className="badge badge-success">{user.data_records} records</span>
                        {!user.is_admin && (
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={e => { e.stopPropagation(); handleDeleteUser(user) }}
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* User data view */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                {activeUser ? `📊 ${activeUser.name}'s Data` : '📊 User Data'}
              </h3>
              {userData && <span className="badge badge-primary">{userData.total_records} records</span>}
            </div>

            {!activeUser ? (
              <div className="empty-state">
                <div className="empty-icon">👆</div>
                <h3>Select a user</h3>
                <p>Click on any user to view their business data.</p>
              </div>
            ) : !userData ? (
              <div className="loading-overlay">
                <div className="loading-spinner"></div> Loading...
              </div>
            ) : userData.total_records === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <h3>No data</h3>
                <p>{activeUser.name} hasn't uploaded any data yet.</p>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th>Revenue</th>
                      <th>Expenses</th>
                      <th>Growth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userData.data.slice(0, 15).map(row => (
                      <tr key={row.id}>
                        <td>{row.month}</td>
                        <td>{fmt(row.revenue)}</td>
                        <td>{fmt(row.expenses)}</td>
                        <td>{row.customer_growth}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {userData.total_records > 15 && (
                  <p style={{padding:'0.5rem 1rem', fontSize:'0.8rem', color:'var(--text-muted)'}}>
                    Showing 15 of {userData.total_records} records.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
