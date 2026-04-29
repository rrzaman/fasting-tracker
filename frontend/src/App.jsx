import { useState } from 'react'
import './App.css'
import CrescentMoon from './components/CrescentMoon'
import FastingCalendar from './components/FastingCalendar'
import HealthTrends from './components/HealthTrends'
import Settings from './components/Settings'
import StarCanvas from './components/StarCanvas'
import { useDashboardData } from './hooks/useDashboardData'

function App() {
  const [activeTab, setActiveTab] = useState('calendar')
  const [focusDate, setFocusDate] = useState(null)
  const { fastingData, healthData, loadingFasting, loadingHealth, error } = useDashboardData()

  // Extract a Set of dates that have health data to validate calendar clicks
  const healthDates = new Set((healthData || []).map(d => d.date))

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

        {error ? (
          <div className="card card--error" style={{ textAlign: 'center', padding: '3rem' }}>
            <h2 style={{ color: 'var(--prohibited)' }}>Error Loading Data</h2>
            <p>{error}</p>
          </div>
        ) : (
          <div className="card card--glow glassmorphism">
            {activeTab === 'calendar' && (
              <div key="calendar" className="tab-content">
                <FastingCalendar 
                  fastingData={fastingData} 
                  healthDates={healthDates}
                  loading={loadingFasting} 
                  onDateClick={(date) => {
                    setFocusDate(date);
                    setActiveTab('health');
                  }}
                />
              </div>
            )}
            {activeTab === 'health' && (
              <div key="health" className="tab-content">
                <h2 style={{ marginBottom: '1.5rem' }}>Health Trends</h2>
                <HealthTrends 
                  healthData={healthData} 
                  fastingData={fastingData} 
                  loading={loadingHealth}
                  focusDate={focusDate}
                  clearFocus={() => setFocusDate(null)}
                />
              </div>
            )}
            {activeTab === 'settings' && (
              <div key="settings" className="tab-content">
                <Settings healthData={healthData} />
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}

export default App