import { useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import Sidebar from '../components/Sidebar'
import { simulate, getBusinessData } from '../services/api'

export default function Simulation() {
  const [darkMode, setDarkMode] = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [latest,   setLatest]   = useState(null)
  const [form, setForm] = useState({
    revenue: 220000, expenses: 100000,
    marketing_spend: 30000, customer_growth: 15,
    marketing_change_pct: 0, price_change_pct: 0,
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  useEffect(() => {
    getBusinessData().then(res => {
      const data = res.data
      if (data.length > 0) {
        const last = data[data.length - 1]
        setLatest(last)
        setForm(f => ({
          ...f,
          revenue: last.revenue,
          expenses: last.expenses,
          marketing_spend: last.marketing_spend,
          customer_growth: last.customer_growth,
        }))
      }
    }).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await simulate(form)
      setResult(res.data)
      toast.success('✅ Simulation complete!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Simulation failed.')
    } finally {
      setLoading(false)
    }
  }

  const fmt = (n) => `₹${Number(n).toLocaleString('en-IN')}`

  const SliderField = ({ label, field, min, max, step = 1, suffix = '' }) => (
    <div className="form-group">
      <label className="form-label" style={{display:'flex', justifyContent:'space-between'}}>
        <span>{label}</span>
        <strong style={{color:'var(--primary)'}}>
          {suffix === '%' && form[field] >= 0 ? '+' : ''}{form[field]}{suffix}
        </strong>
      </label>
      <input
        type="range"
        min={min} max={max} step={step}
        value={form[field]}
        onChange={e => setForm({...form, [field]: Number(e.target.value)})}
        style={{width:'100%', accentColor:'var(--primary)'}}
      />
      <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.75rem', color:'var(--text-muted)'}}>
        <span>{min}{suffix}</span>
        <span>{max}{suffix}</span>
      </div>
    </div>
  )

  return (
    <div className="app-layout">
      <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} />

      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">🎮 Scenario Simulation</h1>
          <p className="page-subtitle">Test business decisions before applying them</p>
        </div>

        <div className="grid-2">
          {/* Input form */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📊 Current Business Data</h3>
              {latest && <span className="badge badge-primary">{latest.month}</span>}
            </div>

            <form onSubmit={handleSubmit}>
              <div style={{marginBottom:'1rem'}}>
                <p style={{fontSize:'0.8rem', fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:'0.75rem'}}>
                  Current Metrics
                </p>
                {[
                  ['Revenue (₹)', 'revenue', 10000, 1000000, 1000],
                  ['Expenses (₹)', 'expenses', 5000, 900000, 1000],
                  ['Marketing Spend (₹)', 'marketing_spend', 1000, 200000, 500],
                  ['Customer Growth (%)', 'customer_growth', -10, 50, 0.5],
                ].map(([label, field, min, max, step]) => (
                  <SliderField key={field} label={label} field={field} min={min} max={max} step={step} suffix={field === 'customer_growth' ? '%' : ''} />
                ))}
              </div>

              <hr className="divider" />

              <div style={{marginBottom:'1rem'}}>
                <p style={{fontSize:'0.8rem', fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:'0.75rem'}}>
                  Scenario Adjustments
                </p>
                <SliderField label="Marketing Change" field="marketing_change_pct" min={-50} max={100} step={1} suffix="%" />
                <SliderField label="Price Change" field="price_change_pct" min={-50} max={100} step={1} suffix="%" />
              </div>

              <button className="btn btn-primary btn-lg" style={{width:'100%'}} disabled={loading}>
                {loading ? <><span className="spinner"></span> Simulating...</> : '🚀 Run Simulation'}
              </button>
            </form>
          </div>

          {/* Results */}
          <div>
            {result ? (
              <>
                {/* Verdict */}
                <div className={`alert ${result.verdict?.includes('increase') ? 'alert-success' : result.verdict?.includes('decrease') ? 'alert-danger' : 'alert-info'}`}
                  style={{marginBottom:'1rem'}}>
                  <span>{result.verdict?.includes('increase') ? '✅' : result.verdict?.includes('decrease') ? '⚠️' : 'ℹ️'}</span>
                  <span>{result.verdict}</span>
                </div>

                {/* Before vs After */}
                <div className="card" style={{marginBottom:'1rem'}}>
                  <div className="card-header">
                    <h3 className="card-title">📊 Before vs After</h3>
                  </div>
                  <table style={{width:'100%', fontSize:'0.875rem'}}>
                    <thead>
                      <tr>
                        <th style={{padding:'0.5rem', background:'var(--primary)', color:'#fff', borderRadius:'4px 0 0 4px'}}>Metric</th>
                        <th style={{padding:'0.5rem', background:'var(--primary)', color:'#fff'}}>Current</th>
                        <th style={{padding:'0.5rem', background:'var(--primary)', color:'#fff', borderRadius:'0 4px 4px 0'}}>Simulated</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ['Revenue', result.input.revenue, result.simulated.revenue],
                        ['Expenses', result.input.expenses, result.simulated.expenses],
                        ['Profit', result.input.revenue - result.input.expenses, result.simulated.profit],
                        ['Marketing', result.input.marketing_spend, result.simulated.marketing_spend],
                        ['Cust. Growth', result.input.customer_growth + '%', result.simulated.customer_growth.toFixed(1) + '%'],
                      ].map(([label, cur, sim]) => {
                        const isNum = typeof sim === 'number'
                        const better = isNum && sim > cur
                        return (
                          <tr key={label} style={{borderBottom:'1px solid var(--border)'}}>
                            <td style={{padding:'0.6rem', fontWeight:500}}>{label}</td>
                            <td style={{padding:'0.6rem', color:'var(--text-muted)'}}>{isNum ? fmt(cur) : cur}</td>
                            <td style={{padding:'0.6rem', fontWeight:600, color: isNum ? (better ? 'var(--success)' : 'var(--danger)') : 'var(--text)'}}>
                              {isNum ? fmt(sim) : sim}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Delta cards */}
                <div className="grid-2">
                  <div className={`metric-card ${result.delta.revenue_change >= 0 ? 'success' : 'danger'}`}>
                    <div className="metric-label">Revenue Change</div>
                    <div className="metric-value" style={{color: result.delta.revenue_change >= 0 ? 'var(--success)' : 'var(--danger)', fontSize:'1.4rem'}}>
                      {result.delta.revenue_change >= 0 ? '+' : ''}{fmt(result.delta.revenue_change)}
                    </div>
                  </div>
                  <div className={`metric-card ${result.delta.profit_change >= 0 ? 'success' : 'danger'}`}>
                    <div className="metric-label">Profit Change</div>
                    <div className="metric-value" style={{color: result.delta.profit_change >= 0 ? 'var(--success)' : 'var(--danger)', fontSize:'1.4rem'}}>
                      {result.delta.profit_change >= 0 ? '+' : ''}{fmt(result.delta.profit_change)}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="card">
                <div className="empty-state">
                  <div className="empty-icon">🎮</div>
                  <h3>Run a simulation</h3>
                  <p>Adjust the sliders on the left and click Run Simulation to see the projected impact on your business.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}