import { useEffect, useState } from 'react'
import { fetchFastingData, fetchHealthData } from './api'
import './App.css'
import CrescentMoon from './components/CrescentMoon'
import FastingCalendar from './components/FastingCalendar'
import HealthTrends from './components/HealthTrends'
import Settings from './components/Settings'
import StarCanvas from './components/StarCanvas'

function App() {
  const [activeTab, setActiveTab] = useState('calendar')
  const [fastingData, setFastingData] = useState({})
  const [healthData, setHealthData]   = useState([])
  const [dataLoading, setDataLoading] = useState(true)

  useEffect(() => {
    async function loadAll() {
      try {
        const [fasting, health] = await Promise.all([
          fetchFastingData(365, 90),
          fetchHealthData(365),
        ])
        const fastingMap = {}
        fasting.forEach(f => { fastingMap[f.date] = f })
        setFastingData(fastingMap)
        setHealthData(health)
      } catch (err) {
        console.error('Failed to load data:', err)
      } finally {
        setDataLoading(false)
      }
    }
    loadAll()
  }, [])

  return (
    <>
      <StarCanvas />

      <div>
        <header style={{ textAlign: 'center', padding: '3rem 0 2rem' }}>
          <CrescentMoon />
          <p style={{
            color: 'var(--emerald-light)',
            fontFamily: 'var(--font-body)',
            fontSize: '0.85rem',
            letterSpacing: '0.25em',
            marginBottom: '0.75rem',
            opacity: 0.8
          }}>
            بسم الله الرحمن الرحيم
          </p>
          <h1>
            Fasting{' '}
            <span className="text-gold-metallic">Dashboard</span>
          </h1>
          <p style={{
            color: 'var(--text-secondary)',
            marginTop: '0.5rem',
            fontSize: '1.15rem',
            letterSpacing: '0.08em'
          }}>
            Personal health & Islamic fasting tracker
          </p>
        </header>

        <div className="divider">
          <span style={{ color: 'var(--gold)', fontSize: '0.6rem', opacity: 0.6 }}>◆</span>
        </div>

        <nav className="tabs">
          {['calendar', 'health', 'settings'].map(tab => (
            <button
              key={tab}
              className={`tab ${activeTab === tab ? 'tab--active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </nav>

        <div className="card card--glow">
          {activeTab === 'calendar' && (
            <div key="calendar" className="tab-content">
              <FastingCalendar fastingData={fastingData} loading={dataLoading} />
            </div>
          )}
          {activeTab === 'health' && (
            <div key="health" className="tab-content">
              <h2 style={{ marginBottom: '1.5rem' }}>Health Trends</h2>
              <HealthTrends healthData={healthData} fastingData={fastingData} loading={dataLoading} />
            </div>
          )}
          {activeTab === 'settings' && (
            <div key="settings" className="tab-content">
              <Settings />
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default App