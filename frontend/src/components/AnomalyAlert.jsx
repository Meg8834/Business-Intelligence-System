export default function AnomalyAlert({ anomalyData }) {
  if (!anomalyData) return null

  const { anomaly_count, anomalies, total_records } = anomalyData

  if (anomaly_count === 0) {
    return (
      <div className="alert alert-success">
        <span>✅</span>
        <span>No anomalies detected across {total_records} records. Business data looks consistent!</span>
      </div>
    )
  }

  return (
    <div>
      <div className="alert alert-danger">
        <span>🚨</span>
        <span>
          <strong>{anomaly_count} anomalous month(s)</strong> detected out of {total_records} records.
          These could indicate unusual revenue drops or expense spikes.
        </span>
      </div>

      <div style={{display:'flex', flexDirection:'column', gap:'0.5rem'}}>
        {anomalies.map((a, i) => (
          <div key={i} style={{
            padding:'0.75rem 1rem',
            background:'#fff0f0',
            border:'1px solid #fecaca',
            borderLeft:'4px solid var(--danger)',
            borderRadius:8,
            display:'flex',
            justifyContent:'space-between',
            alignItems:'center',
            flexWrap:'wrap',
            gap:'0.5rem',
          }}>
            <div>
              <span style={{fontWeight:700, color:'var(--danger)'}}>{a.month}</span>
              <span className="badge badge-danger" style={{marginLeft:'0.5rem'}}>Anomaly</span>
            </div>
            <div style={{display:'flex', gap:'1rem', fontSize:'0.8rem', color:'var(--text-muted)'}}>
              <span>Revenue: <strong>₹{Number(a.revenue).toLocaleString('en-IN')}</strong></span>
              <span>Expenses: <strong>₹{Number(a.expenses).toLocaleString('en-IN')}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}