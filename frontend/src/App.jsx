import { useState } from 'react'
import './App.css'
import StarCanvas from './components/StarCanvas'
import CrescentMoon from './components/CrescentMoon'
import FastingCalendar from './components/FastingCalendar'

function App() {
  const [activeTab, setActiveTab] = useState('calendar')

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
              <FastingCalendar />
            </div>
          )}
          {activeTab === 'health' && (
            <div key="health" className="tab-content">
              <h2>Health Trends</h2>
              <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
                Health trends component coming soon.
              </p>
            </div>
          )}
          {activeTab === 'settings' && (
            <div key="settings" className="tab-content">
              <h2>Settings</h2>
              <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
                Settings component coming soon.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default App