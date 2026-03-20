import { useState, useEffect, useCallback } from 'react'
import { toast } from 'react-toastify'
import Sidebar from '../components/Sidebar'
import FileUpload from '../components/FileUpload'
import DataTable from '../components/DataTable'
import ChartView from '../components/ChartView'
import ForecastCard from '../components/ForecastCard'
import AnomalyAlert from '../components/AnomalyAlert'
import {
  getBusinessData,
  getForecast,
  getAnomaly,
  getHealth,
  getTips,
  chat,
  sendEmail,
} from '../services/api'

const TABS = ['overview', 'data', 'charts', 'anomaly', 'tips', 'chat', 'reports']

const formatCurrency = (value) => (
  `Rs.${Number(value || 0).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
)

const formatMetricCurrency = (value) => `Rs.${(Math.abs(Number(value || 0)) / 1000).toFixed(0)}K`

const formatPercentChange = (current, previous) => {
  if (previous == null || previous === 0) return null
  return (((current - previous) / Math.abs(previous)) * 100).toFixed(2)
}

export default function Dashboard() {
  const [user] = useState(() => JSON.parse(localStorage.getItem('user') || '{}'))
  const [darkMode, setDarkMode] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [businessData, setBusinessData] = useState([])
  const [forecastData, setForecastData] = useState(null)
  const [anomalyData, setAnomalyData] = useState(null)
  const [healthData, setHealthData] = useState(null)
  const [tipsData, setTipsData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [chatMessages, setChatMessages] = useState([{
    role: 'bot',
    text: 'Hi! I am your Business Intelligence Assistant. Ask me to explain anomalies, compare months, show low-growth months, improve profit, or forecast revenue.',
  }])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [emailAddr, setEmailAddr] = useState('')
  const [emailLoading, setEmailLoading] = useState(false)
  const [animatedVals, setAnimatedVals] = useState({})

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light')
  }, [darkMode])

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [dataRes, forecastRes, anomalyRes, healthRes, tipsRes] = await Promise.allSettled([
        getBusinessData(),
        getForecast(3),
        getAnomaly(),
        getHealth(),
        getTips(),
      ])

      if (dataRes.status === 'fulfilled') setBusinessData(dataRes.value.data)
      if (forecastRes.status === 'fulfilled') setForecastData(forecastRes.value.data)
      if (anomalyRes.status === 'fulfilled') setAnomalyData(anomalyRes.value.data)
      if (healthRes.status === 'fulfilled') {
        setHealthData(healthRes.value.data)
        animateMetrics(healthRes.value.data)
      }
      if (tipsRes.status === 'fulfilled') setTipsData(tipsRes.value.data)
    } catch {
      toast.error('Failed to load data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [fetchAll])

  const animateMetrics = (health) => {
    if (!health) return

    const targets = {
      revenue: health.health?.breakdown?.profit_margin_pct || 0,
      score: health.health?.health_score || 0,
    }

    let start = null
    const step = (ts) => {
      if (!start) start = ts
      const progress = Math.min((ts - start) / 800, 1)

      setAnimatedVals({
        revenue: Math.round(targets.revenue * progress * 10) / 10,
        score: Math.round(targets.score * progress),
      })

      if (progress < 1) requestAnimationFrame(step)
    }

    requestAnimationFrame(step)
  }

  const latest = businessData[businessData.length - 1]
  const previous = businessData[businessData.length - 2]
  const profit = latest ? Number(latest.revenue) - Number(latest.expenses) : 0
  const chatSuggestions = [
    'Explain anomalies',
    'Compare this month with last month',
    'Best and worst month',
    'What should I do to improve profit?',
    'Show only months with low growth',
    'Revenue forecast?',
    ...(user.is_admin ? ['Which user has the highest anomaly count?'] : []),
  ]

  const buildLocalAnomalyReason = (row) => {
    if (!businessData.length) {
      return 'the combination of metrics looked unusual compared with the rest of the data'
    }

    const averages = businessData.reduce((acc, item) => ({
      revenue: acc.revenue + Number(item.revenue || 0),
      expenses: acc.expenses + Number(item.expenses || 0),
      marketing_spend: acc.marketing_spend + Number(item.marketing_spend || 0),
      customer_growth: acc.customer_growth + Number(item.customer_growth || 0),
    }), {
      revenue: 0,
      expenses: 0,
      marketing_spend: 0,
      customer_growth: 0,
    })

    const count = businessData.length
    const baseline = {
      revenue: averages.revenue / count,
      expenses: averages.expenses / count,
      marketing_spend: averages.marketing_spend / count,
      customer_growth: averages.customer_growth / count,
    }

    const reasons = []

    if (Number(row.revenue) < baseline.revenue * 0.75) {
      reasons.push('revenue dropped well below the usual level')
    }
    if (Number(row.expenses) > baseline.expenses * 1.25) {
      reasons.push('expenses spiked above the normal range')
    }
    if (Number(row.marketing_spend) > baseline.marketing_spend * 1.5) {
      reasons.push('marketing spend jumped sharply')
    }
    if (Number(row.customer_growth) < 0) {
      reasons.push('customer growth turned negative')
    } else if (Number(row.customer_growth) < baseline.customer_growth - 5) {
      reasons.push('customer growth slowed noticeably')
    }
    if ((Number(row.revenue) - Number(row.expenses)) < 0) {
      reasons.push('the month ended in a loss')
    }

    return reasons.length
      ? reasons.slice(0, 3).join('; ')
      : 'the combination of metrics looked unusual compared with the rest of the data'
  }

  const getLocalRecommendations = () => {
    const recommendations = []

    if ((healthData?.health?.breakdown?.expense_ratio_pct ?? 0) > 70) {
      recommendations.push('Reduce expenses below 70% of revenue to improve business health.')
    }
    if ((healthData?.health?.breakdown?.marketing_ratio_pct ?? 0) > 20) {
      recommendations.push('Audit marketing spend and reallocate budget toward channels with better returns.')
    }
    if ((latest?.customer_growth ?? 0) < 5) {
      recommendations.push('Invest in customer acquisition and retention to lift growth above 5%.')
    }
    if ((anomalyData?.anomaly_count || 0) > 0) {
      recommendations.push(`Investigate ${anomalyData.anomaly_count} anomalous month(s) to find the operational cause.`)
    }

    const nextRevenue = forecastData?.forecast?.revenue?.[0]
    if (latest && nextRevenue != null && Number(nextRevenue) < Number(latest.revenue)) {
      recommendations.push('Revenue is forecast to soften next month, so review pricing, demand, and campaign performance.')
    }

    if (!recommendations.length && tipsData?.tips?.length) {
      recommendations.push(...tipsData.tips.slice(0, 4).map((tip) => tip.tip))
    }

    if (!recommendations.length) {
      recommendations.push('Business looks healthy. Focus on scaling what is already working.')
    }

    return recommendations.slice(0, 4)
  }

  const getLocalChatFallback = (message) => {
    const msg = message.toLowerCase().trim()
    const anomalyRows = anomalyData?.anomalies || []
    const lowGrowthMonths = businessData.filter((row) => Number(row.customer_growth) < 5)

    if (msg.includes('what is my name') || msg.includes('who am i') || msg.includes('my name')) {
      return `Your name is ${user.name || 'User'}.`
    }

    if (msg.includes('date') || msg.includes('today')) {
      return `Today is ${new Date().toLocaleDateString('en-IN', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })}.`
    }

    if (
      (msg.includes('anom') || msg.includes('risk')) &&
      (msg.includes('explain') || msg.includes('which month') || msg.includes('why') || msg.includes('tell'))
    ) {
      if (!anomalyRows.length) {
        return 'No anomalies detected in your uploaded data.'
      }

      return [
        `${anomalyRows.length} anomalies detected.`,
        ...anomalyRows.slice(0, 3).map((row) => (
          `- ${row.month}: ${buildLocalAnomalyReason(row)}. Revenue ${formatCurrency(row.revenue)}, expenses ${formatCurrency(row.expenses)}, growth ${row.customer_growth}%.`
        )),
      ].join('\n')
    }

    if (msg.includes('best month') || msg.includes('worst month')) {
      if (!businessData.length) {
        return 'No data found. Please upload your CSV first.'
      }

      const enriched = businessData.map((row) => ({
        ...row,
        profit: Number(row.revenue || 0) - Number(row.expenses || 0),
      }))
      const bestMonth = enriched.reduce((best, row) => (row.profit > best.profit ? row : best), enriched[0])
      const worstMonth = enriched.reduce((worst, row) => (row.profit < worst.profit ? row : worst), enriched[0])

      return `Best month by profit was ${bestMonth.month} with profit ${formatCurrency(bestMonth.profit)}. Worst month was ${worstMonth.month} with profit ${formatCurrency(worstMonth.profit)}.`
    }

    if (msg.includes('compare') || msg.includes('last month') || msg.includes('previous month')) {
      if (!latest || !previous) {
        return 'I need at least two months of data to compare periods.'
      }

      const previousProfit = Number(previous.revenue) - Number(previous.expenses)
      const revenueChange = Number(latest.revenue) - Number(previous.revenue)
      const profitChange = profit - previousProfit
      const growthChange = (Number(latest.customer_growth) - Number(previous.customer_growth)).toFixed(2)

      return (
        `Compared with ${previous.month}, ${latest.month} revenue changed by ${formatCurrency(revenueChange)} ` +
        `(${formatPercentChange(Number(latest.revenue), Number(previous.revenue))}%), profit changed by ${formatCurrency(profitChange)} ` +
        `(${formatPercentChange(profit, previousProfit)}%), and customer growth changed by ${growthChange} points.`
      )
    }

    if (
      msg.includes('low growth') ||
      msg.includes('growth below') ||
      msg.includes('show only months with low growth') ||
      msg.includes('filter growth')
    ) {
      if (!lowGrowthMonths.length) {
        return 'No months have low growth. All recorded months are at or above 5% customer growth.'
      }

      return [
        'Months with low growth (<5% customer growth):',
        ...lowGrowthMonths.slice(0, 8).map((row) => (
          `* ${row.month}: growth ${row.customer_growth}%, revenue ${formatCurrency(row.revenue)}, profit ${formatCurrency(Number(row.revenue) - Number(row.expenses))}`
        )),
      ].join('\n')
    }

    if (msg.includes('anom') || msg.includes('risk')) {
      return `${anomalyData?.anomaly_count || 0} anomalies detected.`
    }

    if (msg.includes('health') || msg.includes('score')) {
      const score = healthData?.health?.health_score
      const label = healthData?.health?.label
      if (score != null && label) {
        return `Health Score: ${score}/100 - ${label}.`
      }
    }

    if (msg.includes('profit') || msg.includes('loss')) {
      return `Profit: ${formatCurrency(profit)} (${healthData?.health?.breakdown?.profit_margin_pct ?? 0}% margin).`
    }

    if (msg.includes('revenue') || msg.includes('sales')) {
      if (latest) {
        return `Latest revenue: ${formatCurrency(latest.revenue)} for ${latest.month}.`
      }
    }

    if (msg.includes('forecast') || msg.includes('predict')) {
      const nextRevenue = forecastData?.forecast?.revenue?.[0]
      if (nextRevenue != null) {
        return `Next month forecast: ${formatCurrency(nextRevenue)}.`
      }
    }

    if (msg.includes('improve') || msg.includes('tips') || msg.includes('suggest') || msg.includes('recommend')) {
      return `Recommendations:\n${getLocalRecommendations().map((tip) => `* ${tip}`).join('\n')}`
    }

    return null
  }

  const sendChatMessage = async (message) => {
    const userMsg = message.trim()
    if (!userMsg) return

    setChatInput('')
    setChatMessages((prev) => [...prev, { role: 'user', text: userMsg }])
    setChatLoading(true)

    try {
      const res = await chat(userMsg)
      const fallbackAnswer = getLocalChatFallback(userMsg)
      const answer = res.data.answer?.startsWith('Ask me about:') && fallbackAnswer
        ? fallbackAnswer
        : res.data.answer

      setChatMessages((prev) => [...prev, { role: 'bot', text: answer }])
    } catch {
      const fallbackAnswer = getLocalChatFallback(userMsg)
      setChatMessages((prev) => [...prev, {
        role: 'bot',
        text: fallbackAnswer || 'Could not get response. Try again.',
      }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleChat = async (e) => {
    e.preventDefault()
    await sendChatMessage(chatInput)
  }

  const handleEmailAlert = async () => {
    if (!emailAddr) {
      toast.error('Enter an email address!')
      return
    }

    setEmailLoading(true)
    try {
      const res = await sendEmail(emailAddr)
      toast.success(res.data.message)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Email failed.')
    } finally {
      setEmailLoading(false)
    }
  }

  const handleDownloadReport = () => {
    const token = localStorage.getItem('token')

    fetch('http://localhost:8000/report/download', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `business_report_${Date.now()}.pdf`
        a.click()
        URL.revokeObjectURL(url)
        toast.success('Report downloaded!')
      })
      .catch(() => toast.error('Failed to download report.'))
  }

  return (
    <div className="app-layout">
      <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} />

      <main className="main-content">
        <div
          className="page-header"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <h1 className="page-title">Dashboard</h1>
            <p className="page-subtitle">
              {loading ? 'Loading...' : `${businessData.length} records loaded • Auto-refreshes every 30s`}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button className="btn btn-outline btn-sm" onClick={fetchAll} disabled={loading}>
              {loading ? <span className="spinner" style={{ borderTopColor: 'var(--primary)' }}></span> : 'Refresh'}
            </button>
            <button className="btn btn-primary btn-sm" onClick={handleDownloadReport} disabled={!businessData.length}>
              Download PDF
            </button>
          </div>
        </div>

        {latest && (
          <div className="metrics-grid">
            <div className="metric-card count-up">
              <div className="metric-label">Revenue</div>
              <div className="metric-value">{formatMetricCurrency(latest.revenue)}</div>
              <div className="metric-change up">Latest month</div>
            </div>

            <div className="metric-card success count-up">
              <div className="metric-label">Profit</div>
              <div className="metric-value" style={{ color: profit >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                {formatMetricCurrency(profit)}
              </div>
              <div className={`metric-change ${profit >= 0 ? 'up' : 'down'}`}>
                {profit >= 0 ? 'Profit' : 'Loss'}
              </div>
            </div>

            <div className="metric-card warning count-up">
              <div className="metric-label">Health Score</div>
              <div className="metric-value">{animatedVals.score || healthData?.health?.health_score || '--'}</div>
              <div className="metric-change">{healthData?.health?.label || ''}</div>
            </div>

            <div className={`metric-card ${(anomalyData?.anomaly_count || 0) > 0 ? 'danger' : 'success'} count-up`}>
              <div className="metric-label">Anomalies</div>
              <div className="metric-value">{anomalyData?.anomaly_count ?? '--'}</div>
              <div className={`metric-change ${(anomalyData?.anomaly_count || 0) > 0 ? 'down' : 'up'}`}>
                {(anomalyData?.anomaly_count || 0) > 0 ? 'Detected' : 'All clear'}
              </div>
            </div>
          </div>
        )}

        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
            marginBottom: '1.5rem',
            flexWrap: 'wrap',
            borderBottom: '1px solid var(--border)',
            paddingBottom: '0.75rem',
          }}
        >
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.4rem 1rem',
                borderRadius: 8,
                border: activeTab === tab ? '1.5px solid var(--primary)' : '1.5px solid var(--border)',
                background: activeTab === tab ? 'var(--primary)' : 'transparent',
                color: activeTab === tab ? '#fff' : 'var(--text-muted)',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 500,
                fontFamily: 'var(--font-body)',
                textTransform: 'capitalize',
                transition: 'all 0.2s',
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="fade-in" key={activeTab}>
          {activeTab === 'overview' && (
            <div className="grid-2">
              <FileUpload onUploadSuccess={fetchAll} />
              <ForecastCard healthData={healthData} />
            </div>
          )}

          {activeTab === 'data' && (
            <DataTable data={businessData} anomalyData={anomalyData} />
          )}

          {activeTab === 'charts' && (
            <ChartView
              forecastData={forecastData}
              businessData={businessData}
              anomalyData={anomalyData}
            />
          )}

          {activeTab === 'anomaly' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Anomaly Detection</h3>
                <span className="badge badge-danger">
                  {anomalyData?.anomaly_count || 0} anomalies
                </span>
              </div>
              <AnomalyAlert anomalyData={anomalyData} />
            </div>
          )}

          {activeTab === 'tips' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Business Tips</h3>
                {tipsData && (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {tipsData.critical_count > 0 && (
                      <span className="badge badge-danger">{tipsData.critical_count} critical</span>
                    )}
                    {tipsData.high_priority_count > 0 && (
                      <span className="badge badge-warning">{tipsData.high_priority_count} high</span>
                    )}
                  </div>
                )}
              </div>

              {tipsData?.tips?.map((tip, i) => (
                <div key={i} className={`tip-card ${tip.priority}`}>
                  <div className="tip-header">
                    <span className="tip-category">{tip.category}</span>
                    <span className={`badge badge-${tip.priority}`}>{tip.priority}</span>
                  </div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text)', lineHeight: 1.5 }}>{tip.tip}</p>
                </div>
              ))}

              {!tipsData?.tips?.length && (
                <div className="empty-state">
                  <div className="empty-icon">Tips</div>
                  <h3>No tips yet</h3>
                  <p>Upload data to get business recommendations.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">AI Business Assistant</h3>
                <span className="badge badge-primary">Powered by AI</span>
              </div>

              <div className="chat-container">
                <div className="chat-messages" id="chat-messages">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-msg ${msg.role}`}>
                      {msg.text}
                    </div>
                  ))}

                  {chatLoading && (
                    <div className="chat-msg bot">
                      <span className="loading-spinner" style={{ width: 16, height: 16, borderWidth: 2 }}></span>
                    </div>
                  )}
                </div>

                <form onSubmit={handleChat} className="chat-input-row">
                  <input
                    className="form-control"
                    placeholder="Ask: Explain anomalies, compare months, low growth, improve profit..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={chatLoading}
                  />
                  <button className="btn btn-primary" disabled={chatLoading || !chatInput.trim()}>
                    Send
                  </button>
                </form>
              </div>

              <div style={{ marginTop: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {chatSuggestions.map((question) => (
                  <button
                    key={question}
                    className="btn btn-outline btn-sm"
                    onClick={() => { sendChatMessage(question) }}
                    disabled={chatLoading}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'reports' && (
            <div className="grid-2">
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">PDF Report</h3>
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.6 }}>
                  Download a complete PDF report including health score, forecast, anomalies, AI insights and historical data table.
                </p>
                <button
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  onClick={handleDownloadReport}
                  disabled={!businessData.length}
                >
                  Download PDF Report
                </button>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Email Anomaly Alert</h3>
                </div>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.6 }}>
                  Send an email alert to any address with details of detected anomalies.
                </p>
                <div className="form-group">
                  <label className="form-label">Recipient Email</label>
                  <input
                    className="form-control"
                    type="email"
                    placeholder="recipient@email.com"
                    value={emailAddr}
                    onChange={(e) => setEmailAddr(e.target.value)}
                  />
                </div>
                <button
                  className="btn btn-danger"
                  style={{ width: '100%' }}
                  onClick={handleEmailAlert}
                  disabled={emailLoading || !emailAddr || !businessData.length}
                >
                  {emailLoading
                    ? <><span className="spinner"></span> Sending...</>
                    : 'Send Anomaly Alert'}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
