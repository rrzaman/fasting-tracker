import { useState } from 'react'
import './App.css'
import CrescentMoon from './components/CrescentMoon'
import FastingCalendar from './components/FastingCalendar'
import HealthTrends from './components/HealthTrends'
import Settings from './components/Settings'
import StarCanvas from './components/StarCanvas'
import { useDashboardData } from './hooks/useDashboardData'
import { useAuth } from 'react-oidc-context'
import { demoFastingData, demoHealthData } from './demoData'
import DemoBanner from './components/DemoBanner'

function App() {
  const auth = useAuth()
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [activeTab, setActiveTab] = useState('calendar')
  const [focusDate, setFocusDate] = useState(null)

  const realData = useDashboardData()

  if (auth.isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        width: '100vw',
        background: 'var(--bg-primary)',
        color: 'var(--text-secondary)',
        fontFamily: 'var(--font-body)',
        position: 'fixed',
        top: 0,
        left: 0,
      }}>
        Loading...
      </div>
    )
  }

  if (!auth.isAuthenticated && !isDemoMode) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'var(--bg-primary)',
        gap: '1.5rem',
      }}>
        <CrescentMoon />
        <h1 style={{ fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}>
          Fasting <span className="text-gold-metallic">Dashboard</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Personal health & Islamic fasting tracker
        </p>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={() => auth.signinRedirect()}
            style={{
              background: 'rgba(240,192,64,0.1)',
              border: '1px solid var(--gold)',
              borderRadius: '8px',
              color: 'var(--gold)',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9rem',
              padding: '0.75rem 2rem',
              transition: 'all 0.2s ease',
            }}
          >
            Sign in
          </button>
          <button
            onClick={() => setIsDemoMode(true)}
            style={{
              background: 'rgba(61,189,128,0.1)',
              border: '1px solid var(--emerald)',
              borderRadius: '8px',
              color: 'var(--emerald-light)',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9rem',
              padding: '0.75rem 2rem',
              transition: 'all 0.2s ease',
            }}
          >
            Try Demo
          </button>
        </div>
      </div>
    )
  }


  const fastingData = isDemoMode ? demoFastingData : realData.fastingData
  const healthData = isDemoMode ? demoHealthData : realData.healthData
  const loadingFasting = isDemoMode ? false : realData.loadingFasting
  const loadingHealth = isDemoMode ? false : realData.loadingHealth
  const error = isDemoMode ? null : realData.error

  // Extract a Set of dates that have health data to validate calendar clicks
  const healthDates = new Set((healthData || []).map(d => d.date))

  return (
    <>
      <StarCanvas />

      {isDemoMode && (
        <DemoBanner onExit={() => setIsDemoMode(false)} />
      )}

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
                <Settings
                  healthData={healthData}
                  isDemoMode={isDemoMode}
                  onSignOut={() => auth.signoutRedirect()} />
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}

export default App