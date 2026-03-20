import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { login } from '../services/api'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm]       = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await login(form)
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user',  JSON.stringify(res.data.user))
      toast.success('Welcome back ' + res.data.user.name)
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card fade-in">
        <div className="auth-logo">
          <h1>ML Business Intelligence</h1>
          <p>Business Decision Intelligence System</p>
        </div>
        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-subtitle">Sign in to your account</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              className="form-control"
              type="email"
              placeholder="your@email.com"
              value={form.email}
              onChange={e => setForm({...form, email: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-control"
              type="password"
              placeholder="Enter password"
              value={form.password}
              onChange={e => setForm({...form, password: e.target.value})}
              required
            />
          </div>
          <button
            className="btn btn-primary btn-lg"
            style={{width:'100%'}}
            disabled={loading}
          >
            {loading
              ? <><span className="spinner"></span> Signing in...</>
              : 'Sign In'
            }
          </button>
        </form>
        <div className="auth-footer">
          Do not have an account?{' '}
          <a onClick={() => navigate('/register')}>Create one</a>
        </div>
        <hr className="divider" />
        <div style={{fontSize:'0.8rem', color:'var(--text-muted)', textAlign:'center'}}>
          <strong>Admin login:</strong> admin@business.com / admin123
        </div>
      </div>
    </div>
  )
}