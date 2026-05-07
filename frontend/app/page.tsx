'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, user, logout, isLoading } = useAuth()

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div className="google-loader">
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
        </div>
      </div>
    )
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null
  }

  return (
    <>
      {/* Top Navigation Bar - EXACT portfolio style */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid var(--border-light)',
        boxShadow: '0 1px 6px rgba(32,33,36,.12)',
        padding: '0 40px',
        height: '64px'
      }}>
        <div style={{
          maxWidth: '1400px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '100%'
        }}>
          <div style={{
            fontFamily: "'Product Sans', 'Google Sans', sans-serif",
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--text-primary)'
          }}>
            LMARO
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '15px',
              color: 'var(--text-secondary)',
              marginRight: '8px'
            }}>
              Hi, <strong>{user?.full_name?.split(' ')[0]}</strong>
            </span>
            <Link href="/dashboard">
              <button className="btn-google btn-google-secondary">
                Dashboard
              </button>
            </Link>
            <button 
              onClick={() => {
                logout()
                router.push('/login')
              }}
              className="btn-google btn-google-secondary"
              style={{
                padding: '10px 24px'
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Mesh Background - EXACT portfolio style */}
      <div className="mesh-bg">
        <div className="mesh-orb mesh-orb-1"></div>
        <div className="mesh-orb mesh-orb-2"></div>
        <div className="mesh-orb mesh-orb-3"></div>
        <div className="mesh-orb mesh-orb-4"></div>
      </div>

      {/* Main Content - EXACT portfolio hero style */}
      <main style={{ 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        zIndex: 1,
        padding: '80px 40px 40px'
      }}>
        <div style={{ maxWidth: '900px', textAlign: 'center' }}>
          {/* Logo/Title - EXACT portfolio name styling */}
          <h1 style={{ 
            fontFamily: "'Product Sans', 'Google Sans', sans-serif", 
            fontSize: 'clamp(3rem, 10vw, 5.5rem)', 
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: '24px',
            lineHeight: 1.1
          }}>
            LMARO
          </h1>

          {/* Tagline - EXACT portfolio subtitle styling */}
          <h2 style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '1.5rem',
            fontWeight: 400,
            color: 'var(--text-secondary)',
            marginBottom: '32px',
            lineHeight: 1.3
          }}>
            AI-Powered Resume Optimizer
          </h2>

          {/* Description - EXACT portfolio description styling */}
          <p style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '1.1rem',
            fontWeight: 400,
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
            marginBottom: '48px',
            maxWidth: '700px',
            margin: '0 auto 48px'
          }}>
            Generate tailored, ATS-optimized resumes using advanced AI. 
            Our multi-agent system evaluates, optimizes, and verifies your resume 
            to match any job description perfectly.
          </p>

          {/* Feature Stats - EXACT portfolio stat card layout */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '16px',
            maxWidth: '700px',
            margin: '0 auto 48px'
          }}>
            <StatCard number="90+" label="Match Score" colorIndex={1} />
            <StatCard number="100%" label="Factually Accurate" colorIndex={2} />
            <StatCard number="3x" label="Faster Process" colorIndex={3} />
            <StatCard number="∞" label="Iterations" colorIndex={4} />
          </div>

          {/* CTA Button - EXACT portfolio button style */}
          <div className="cta-buttons" style={{
            display: 'flex',
            gap: '16px',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={() => router.push('/generate')}
              className="btn-google btn-google-primary"
              style={{ 
                fontSize: '1rem',
                padding: '12px 32px'
              }}
            >
              <span className="material-icons" style={{ fontSize: '20px' }}>rocket_launch</span>
              <span>Generate Resume</span>
            </button>
            <Link href="/dashboard">
              <button className="btn-google btn-google-secondary">
                <span className="material-icons" style={{ fontSize: '20px' }}>dashboard</span>
                <span>View Dashboard</span>
              </button>
            </Link>
          </div>

          {/* Features Chips - EXACT portfolio chip styling WITH ICONS */}
          <div style={{ 
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            justifyContent: 'center',
            marginTop: '48px',
            maxWidth: '800px',
            margin: '48px auto 0'
          }}>
            <FeatureChip icon="verified_user" text="Factuality Checked" />
            <FeatureChip icon="trending_up" text="90+ Score Guaranteed" />
            <FeatureChip icon="description" text="DOCX Export" />
            <FeatureChip icon="speed" text="30-60 Seconds" />
            <FeatureChip icon="psychology" text="AI-Powered" />
            <FeatureChip icon="groups" text="Multi-Agent System" />
          </div>
        </div>
      </main>
    </>
  )
}

// EXACT portfolio stat card component
function StatCard({ number, label, colorIndex }: { number: string, label: string, colorIndex: number }) {
  const colors = ['', 'var(--google-blue)', 'var(--google-red)', 'var(--google-yellow)', 'var(--google-green)']
  const color = colors[colorIndex]
  
  return (
    <div 
      className="stat-card card-google"
      style={{ 
        padding: '24px',
        textAlign: 'center',
        transition: 'all 0.2s ease'
      }}
    >
      <span style={{ 
        fontFamily: "'Product Sans', 'Google Sans', sans-serif",
        fontSize: '2rem',
        fontWeight: 700,
        color: color,
        marginBottom: '4px',
        display: 'block'
      }}>
        {number}
      </span>
      <span style={{
        fontFamily: "'Google Sans', sans-serif",
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        fontWeight: 400
      }}>
        {label}
      </span>
    </div>
  )
}

// EXACT portfolio chip component WITH ICONS
function FeatureChip({ icon, text }: { icon: string, text: string }) {
  return (
    <span style={{
      fontFamily: "'Google Sans', sans-serif",
      padding: '8px 16px',
      background: 'var(--bg-light)',
      borderRadius: '16px',
      fontSize: '0.875rem',
      color: 'var(--text-secondary)',
      border: '1px solid var(--border-light)',
      transition: 'all 0.2s ease',
      cursor: 'default',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.background = 'white'
      e.currentTarget.style.borderColor = 'var(--google-blue)'
      e.currentTarget.style.color = 'var(--google-blue)'
      e.currentTarget.style.transform = 'translateY(-2px)'
      e.currentTarget.style.boxShadow = '0 2px 4px rgba(66, 133, 244, 0.2)'
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.background = 'var(--bg-light)'
      e.currentTarget.style.borderColor = 'var(--border-light)'
      e.currentTarget.style.color = 'var(--text-secondary)'
      e.currentTarget.style.transform = 'translateY(0)'
      e.currentTarget.style.boxShadow = 'none'
    }}
    >
      <span className="material-icons" style={{ fontSize: '18px' }}>{icon}</span>
      {text}
    </span>
  )
}
