import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
)

const COLORS = {
  primary:  '#4361ee',
  accent:   '#f72585',
  success:  '#2dc653',
  warning:  '#f4a261',
  danger:   '#e63946',
  muted:    'rgba(67,97,238,0.15)',
}

export default function ChartView({ forecastData, businessData, anomalyData }) {
  if (!forecastData || !businessData?.length) {
    return (
      <div className="card">
        <div className="card-header"><h3 className="card-title">📈 Charts</h3></div>
        <div className="empty-state">
          <div className="empty-icon">📉</div>
          <h3>No chart data</h3>
          <p>Upload data to see charts.</p>
        </div>
      </div>
    )
  }

  const months   = forecastData.historical?.months   || []
  const revenues = forecastData.historical?.revenue  || []
  const fMonths  = forecastData.forecast?.months     || []
  const fRevs    = forecastData.forecast?.revenue    || []
  const fLower   = forecastData.forecast?.lower_band || []
  const fUpper   = forecastData.forecast?.upper_band || []

  const anomalyMonths = new Set(
    (anomalyData?.anomalies || []).map(a => a.month)
  )

  // Revenue + forecast line chart
  const allMonths = [...months, ...fMonths]
  const allRevs   = [...revenues, ...Array(fMonths.length).fill(null)]
  const forecastLine = [...Array(months.length).fill(null), ...fRevs]
  const upperBand    = [...Array(months.length).fill(null), ...fUpper]
  const lowerBand    = [...Array(months.length).fill(null), ...fLower]

  const pointColors = months.map(m =>
    anomalyMonths.has(m) ? COLORS.danger : COLORS.primary
  )

  const lineData = {
    labels: allMonths,
    datasets: [
      {
        label: 'Historical Revenue',
        data: allRevs,
        borderColor: COLORS.primary,
        backgroundColor: COLORS.muted,
        pointBackgroundColor: [...pointColors, ...Array(fMonths.length).fill(COLORS.primary)],
        pointRadius: 5,
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Forecast',
        data: forecastLine,
        borderColor: COLORS.accent,
        borderDash: [6,3],
        pointBackgroundColor: COLORS.accent,
        pointRadius: 5,
        tension: 0.4,
        fill: false,
      },
      {
        label: 'Upper Band',
        data: upperBand,
        borderColor: 'rgba(247,37,133,0.2)',
        backgroundColor: 'rgba(247,37,133,0.08)',
        pointRadius: 0,
        fill: '+1',
        tension: 0.4,
      },
      {
        label: 'Lower Band',
        data: lowerBand,
        borderColor: 'rgba(247,37,133,0.2)',
        pointRadius: 0,
        fill: false,
        tension: 0.4,
      },
    ]
  }

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => `₹${Number(ctx.raw).toLocaleString('en-IN')}`
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: v => `₹${(v/1000).toFixed(0)}K`
        }
      }
    }
  }

  // Expenses vs Revenue bar chart
  const barData = {
    labels: businessData.map(d => d.month),
    datasets: [
      {
        label: 'Revenue',
        data: businessData.map(d => d.revenue),
        backgroundColor: COLORS.primary,
        borderRadius: 6,
      },
      {
        label: 'Expenses',
        data: businessData.map(d => d.expenses),
        backgroundColor: COLORS.warning,
        borderRadius: 6,
      },
      {
        label: 'Marketing',
        data: businessData.map(d => d.marketing_spend),
        backgroundColor: COLORS.accent,
        borderRadius: 6,
      },
    ]
  }

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => `₹${Number(ctx.raw).toLocaleString('en-IN')}`
        }
      }
    },
    scales: {
      y: {
        ticks: { callback: v => `₹${(v/1000).toFixed(0)}K` }
      },
      x: {
        ticks: { maxRotation: 45 }
      }
    }
  }

  return (
    <>
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📈 Revenue Forecast</h3>
          <div style={{display:'flex', gap:'0.75rem', fontSize:'0.8rem'}}>
            <span style={{display:'flex',alignItems:'center',gap:4}}>
              <span style={{width:12,height:3,background:COLORS.primary,display:'inline-block',borderRadius:2}}></span>
              Historical
            </span>
            <span style={{display:'flex',alignItems:'center',gap:4}}>
              <span style={{width:12,height:3,background:COLORS.accent,display:'inline-block',borderRadius:2}}></span>
              Forecast
            </span>
            <span style={{display:'flex',alignItems:'center',gap:4}}>
              <span style={{width:10,height:10,background:COLORS.danger,borderRadius:'50%',display:'inline-block'}}></span>
              Anomaly
            </span>
          </div>
        </div>
        <div style={{height:280}}>
          <Line data={lineData} options={lineOptions} />
        </div>
      </div>

      <div className="card" style={{marginTop:'1.5rem'}}>
        <div className="card-header">
          <h3 className="card-title">📊 Revenue vs Expenses vs Marketing</h3>
          <div style={{display:'flex', gap:'0.75rem', fontSize:'0.8rem'}}>
            {[['Revenue', COLORS.primary], ['Expenses', COLORS.warning], ['Marketing', COLORS.accent]].map(([l,c]) => (
              <span key={l} style={{display:'flex',alignItems:'center',gap:4}}>
                <span style={{width:10,height:10,background:c,borderRadius:2,display:'inline-block'}}></span>
                {l}
              </span>
            ))}
          </div>
        </div>
        <div style={{height:280}}>
          <Bar data={barData} options={barOptions} />
        </div>
      </div>
    </>
  )
}