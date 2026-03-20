import { useState, useRef } from 'react'
import { toast } from 'react-toastify'
import { uploadCSV, downloadSampleCSV } from '../services/api'

export default function FileUpload({ onUploadSuccess }) {
  const [loading,  setLoading]  = useState(false)
  const [mode,     setMode]     = useState('replace')
  const [dragOver, setDragOver] = useState(false)
  const [fileName, setFileName] = useState('')
  const fileRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    if (!file.name.endsWith('.csv')) {
      toast.error('Only .csv files are accepted!')
      return
    }
    setFileName(file.name)
    setLoading(true)
    try {
      const res = await uploadCSV(file, mode)
      toast.success(`✅ ${res.data.rows_inserted} rows uploaded successfully!`)
      if (res.data.warnings?.length > 0) {
        res.data.warnings.forEach(w => toast.warning(`⚠️ ${w}`))
      }
      onUploadSuccess?.()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📤 Upload Business Data</h3>
        <a
          href={downloadSampleCSV()}
          download="sample_business_data.csv"
          className="btn btn-outline btn-sm"
        >
          ⬇️ Sample CSV
        </a>
      </div>

      {/* Mode selector */}
      <div style={{display:'flex', gap:'1rem', marginBottom:'1rem'}}>
        {['replace','append'].map(m => (
          <label key={m} style={{display:'flex', alignItems:'center', gap:'6px', cursor:'pointer', fontSize:'0.875rem'}}>
            <input
              type="radio"
              value={m}
              checked={mode === m}
              onChange={() => setMode(m)}
            />
            <span>
              {m === 'replace' ? '🔄 Replace (fresh start)' : '➕ Append (add to existing)'}
            </span>
          </label>
        ))}
      </div>

      {/* Drop zone */}
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => {
          e.preventDefault()
          setDragOver(false)
          handleFile(e.dataTransfer.files[0])
        }}
      >
        <div className="upload-icon">📁</div>
        {fileName
          ? <p style={{fontWeight:500, color:'var(--primary)'}}>{fileName}</p>
          : <>
              <p className="upload-text">Drag & drop your CSV here</p>
              <p className="upload-text" style={{fontSize:'0.8rem'}}>or click to browse</p>
            </>
        }
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          style={{display:'none'}}
          onChange={e => handleFile(e.target.files[0])}
        />
      </div>

      {fileName && (
        <button
          className="btn btn-primary"
          style={{width:'100%', marginTop:'1rem'}}
          disabled={loading}
          onClick={() => fileRef.current?.click()}
        >
          {loading ? <><span className="spinner"></span> Uploading...</> : '📤 Upload CSV'}
        </button>
      )}

      <div className="alert alert-info" style={{marginTop:'1rem', marginBottom:0}}>
        <span>💡</span>
        <span>Accepted columns: month, revenue, expenses, marketing_spend, customer_growth.
        Also accepts: sales, income, costs, ads, new_customers and more.</span>
      </div>
    </div>
  )
}