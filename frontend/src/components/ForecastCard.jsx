export default function HealthScore({ healthData }) {
  if (!healthData) return null

  const score = healthData.health?.health_score || 0
  const label = healthData.health?.label || ''
  const breakdown = healthData.health?.breakdown || {}
  const insights = healthData.explanation?.insights || []

  const color = score >= 80 ? '#2dc653'
              : score >= 60 ? '#f4a261'
              : score >= 40 ? '#f72585'
              : '#e63946'

  const circumference = 2 * Math.PI * 54
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">💚 Business Health Score</h3>
        <span style={{fontSize:'0.85rem', color:'var(--text-muted)'}}>
          {healthData.latest_month}
        </span>
      </div>

      <div style={{display:'flex', gap:'2rem', alignItems:'center', flexWrap:'wrap'}}>
        {/* SVG Gauge */}
        <div style={{textAlign:'center', flexShrink:0}}>
          <svg width="140" height="140" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="54"
              fill="none" stroke="var(--border)" strokeWidth="10" />
            <circle cx="60" cy="60" r="54"
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
              style={{transition:'stroke-dashoffset 1s ease'}}
            />
            <text x="60" y="55" textAnchor="middle"
              fill={color}
              fontSize="22" fontWeight="800"
              fontFamily="'Syne', sans-serif">
              {score}
            </text>
            <text x="60" y="72" textAnchor="middle"
              fill="var(--text-muted)" fontSize="9">
              out of 100
            </text>
          </svg>
          <div style={{
            display:'inline-block', padding:'4px 16px',
            background:color+'22', color, borderRadius:999,
            fontSize:'0.85rem', fontWeight:700
          }}>
            {label}
          </div>
        </div>

        {/* Breakdown */}
        <div style={{flex:1, minWidth:200}}>
          {[
            ['Profit Margin',    breakdown.profit_margin_score,       breakdown.profit_margin_pct + '%'],
            ['Expense Ratio',    breakdown.expense_ratio_score,       breakdown.expense_ratio_pct + '%'],
            ['Marketing Eff.',   breakdown.marketing_efficiency_score, breakdown.marketing_ratio_pct + '%'],
            ['Customer Growth',  breakdown.customer_growth_score,     breakdown.customer_growth_value + '%'],
          ].map(([label, score, val]) => (
            <div key={label} style={{marginBottom:'0.6rem'}}>
              <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.8rem', marginBottom:3}}>
                <span style={{color:'var(--text-muted)'}}>{label}</span>
                <span style={{fontWeight:600}}>{score}/25 <span style={{color:'var(--text-muted)', fontWeight:400}}>({val})</span></span>
              </div>
              <div style={{height:6, background:'var(--border)', borderRadius:3, overflow:'hidden'}}>
                <div style={{
                  height:'100%',
                  width:`${(score/25)*100}%`,
                  background: score >= 20 ? '#2dc653' : score >= 13 ? '#f4a261' : '#e63946',
                  borderRadius:3,
                  transition:'width 1s ease'
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <div style={{marginTop:'1rem', borderTop:'1px solid var(--border)', paddingTop:'1rem'}}>
          <p style={{fontSize:'0.8rem', fontWeight:600, color:'var(--text-muted)', marginBottom:'0.5rem', textTransform:'uppercase', letterSpacing:'0.05em'}}>
            AI Insights
          </p>
          {insights.slice(0,3).map((insight, i) => (
            <p key={i} style={{fontSize:'0.85rem', color:'var(--text)', marginBottom:'0.4rem', lineHeight:1.5}}>
              • {insight}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}