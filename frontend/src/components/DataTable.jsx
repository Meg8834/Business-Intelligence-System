import { useState } from 'react'

export default function DataTable({ data, anomalyData }) {
  const [sortField, setSortField] = useState('id')
  const [sortDir,   setSortDir]   = useState('asc')

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-header"><h3 className="card-title">📋 Business Data</h3></div>
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <h3>No data yet</h3>
          <p>Upload a CSV file to see your business data here.</p>
        </div>
      </div>
    )
  }

  const anomalyIds = new Set(
    (anomalyData?.anomalies || []).map(a => a.id)
  )

  const sorted = [...data].sort((a, b) => {
    const va = a[sortField], vb = b[sortField]
    if (sortDir === 'asc') return va > vb ? 1 : -1
    return va < vb ? 1 : -1
  })

  const handleSort = (field) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortField(field); setSortDir('asc') }
  }

  const arrow = (field) => sortField === field ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''

  const fmt = (n) => `₹${Number(n).toLocaleString('en-IN')}`

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📋 Business Data</h3>
        <span className="badge badge-primary">{data.length} records</span>
      </div>

      <div style={{display:'flex', gap:'0.5rem', marginBottom:'0.75rem', flexWrap:'wrap'}}>
        <span style={{display:'flex', alignItems:'center', gap:'4px', fontSize:'0.8rem', color:'var(--text-muted)'}}>
          <span style={{width:12,height:12,background:'#fee2e2',borderRadius:2,display:'inline-block'}}></span>
          Anomaly detected
        </span>
        <span style={{display:'flex', alignItems:'center', gap:'4px', fontSize:'0.8rem', color:'var(--text-muted)'}}>
          <span style={{width:12,height:12,background:'#fef3c7',borderRadius:2,display:'inline-block'}}></span>
          Expenses &gt; 80% revenue
        </span>
        <span style={{display:'flex', alignItems:'center', gap:'4px', fontSize:'0.8rem', color:'var(--text-muted)'}}>
          <span style={{width:12,height:12,background:'#dcfce7',borderRadius:2,display:'inline-block'}}></span>
          Healthy month
        </span>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              {['month','revenue','expenses','marketing_spend','customer_growth'].map(f => (
                <th key={f} onClick={() => handleSort(f)} style={{cursor:'pointer', userSelect:'none'}}>
                  {f.replace('_',' ')}{arrow(f)}
                </th>
              ))}
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(row => {
              const isAnomaly  = anomalyIds.has(row.id)
              const expRatio   = row.revenue > 0 ? row.expenses / row.revenue : 0
              const isHighExp  = expRatio > 0.8
              const isHealthy  = !isAnomaly && !isHighExp && row.revenue > row.expenses

              let rowClass = ''
              let rowStyle = {}
              if (isAnomaly)       { rowClass = 'anomaly-row'; rowStyle = {background:'#fff0f0'} }
              else if (isHighExp)  { rowStyle = {background:'#fffbeb'} }
              else if (isHealthy)  { rowStyle = {background:'#f0fdf4'} }

              return (
                <tr key={row.id} className={rowClass} style={rowStyle}>
                  <td style={{fontWeight:500}}>{row.month}</td>
                  <td>{fmt(row.revenue)}</td>
                  <td>{fmt(row.expenses)}</td>
                  <td>{fmt(row.marketing_spend)}</td>
                  <td>{row.customer_growth}%</td>
                  <td>
                    {isAnomaly
                      ? <span className="badge badge-danger">🚨 Anomaly</span>
                      : isHighExp
                        ? <span className="badge badge-warning">⚠️ High Exp</span>
                        : <span className="badge badge-success">✅ Healthy</span>
                    }
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}