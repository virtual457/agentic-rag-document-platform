'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { GenerationModal } from '@/components/GenerationModal'

export default function GeneratePage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading } = useAuth()
  const [jdText, setJdText] = useState('')
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [currentStage, setCurrentStage] = useState('')
  const [currentMessage, setCurrentMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const [profileCompletion, setProfileCompletion] = useState<number | null>(null)
  const [showWarning, setShowWarning] = useState(false)

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    } else if (token) {
      checkProfileCompletion()
    }
  }, [isAuthenticated, isLoading, token, router])

  const checkProfileCompletion = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/profile/completion', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()
      setProfileCompletion(data.percentage)
    } catch (error) {
      console.error(error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Check profile completion
    if (profileCompletion !== null && profileCompletion < 70) {
      setShowWarning(true)
      return
    }
    
    if (!jdText.trim() || !company.trim() || !role.trim()) {
      alert('Please fill in all fields')
      return
    }

    setIsGenerating(true)
    setProgress(0)
    
    try {
      const response = await fetch('http://localhost:8000/api/generate/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'chandan',
          jd_text: jdText,
          company: company,
          role: role,
          optimize: true,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate resume')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6)
            try {
              const update = JSON.parse(jsonStr)
              
              setCurrentStage(update.stage)
              setCurrentMessage(update.message)
              setProgress(update.progress || 0)

              if (update.stage === 'complete' && update.data) {
                setTimeout(() => {
                  // Store results in sessionStorage
                  sessionStorage.setItem('resumeData', JSON.stringify(update.data))
                  router.push('/results')
                }, 1000)
              }

              if (update.stage === 'error') {
                alert(`Error: ${update.error}`)
                setIsGenerating(false)
              }
            } catch (e) {
              console.error('Failed to parse SSE message:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error generating resume:', error)
      alert('Failed to generate resume. Please try again.')
      setIsGenerating(false)
    }
  }

  const handlePasteSample = () => {
    setJdText(`We are seeking a talented Software Engineer Intern to join our team for Spring/Summer 2026.

Responsibilities:
- Design and develop scalable backend systems using modern frameworks
- Collaborate with cross-functional teams on feature development
- Write clean, maintainable, and well-documented code
- Participate in code reviews and contribute to team discussions
- Debug and optimize application performance

Requirements:
- Currently pursuing MS in Computer Science or related field
- Strong proficiency in Python, Java, or Go
- Experience with distributed systems and cloud technologies
- Knowledge of databases, APIs, and microservices architecture
- Excellent problem-solving and communication skills
- Previous internship or co-op experience preferred`)
    setCompany('Google')
    setRole('Software Engineer Intern')
  }

  return (
    <>
      {/* Mesh Background */}
      <div className="mesh-bg">
        <div className="mesh-orb mesh-orb-1"></div>
        <div className="mesh-orb mesh-orb-2"></div>
        <div className="mesh-orb mesh-orb-3"></div>
        <div className="mesh-orb mesh-orb-4"></div>
      </div>

      {/* Generation Modal */}
      <GenerationModal 
        stage={currentStage}
        message={currentMessage}
        progress={progress}
        isOpen={isGenerating}
      />

      {/* Header */}
      <header style={{ 
        borderBottom: '1px solid var(--border-light)', 
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        boxShadow: '0 1px 6px rgba(32,33,36,.12)'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
            <button 
              onClick={() => router.push('/')}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start'
              }}
            >
              <h1 style={{ 
                fontFamily: "'Product Sans', sans-serif", 
                fontSize: '1.75rem', 
                fontWeight: 700,
                color: 'var(--text-primary)'
              }}>
                LMARO
              </h1>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                AI-Powered Resume Optimizer
              </p>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ 
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        zIndex: 1,
        padding: '40px'
      }}>
        <div style={{ maxWidth: '900px', width: '100%' }}>
          <div className="card-google p-8">
            <form onSubmit={handleSubmit}>
              {/* Title */}
              <h2 style={{
                fontFamily: 'Product Sans, sans-serif',
                fontSize: '2rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '32px',
                textAlign: 'center'
              }}>
                Generate Your Resume
              </h2>

              {/* Company and Role */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                <div>
                  <label htmlFor="company" style={{ 
                    display: 'block',
                    fontFamily: 'Google Sans, sans-serif',
                    fontSize: '0.95rem',
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}>
                    Company Name
                  </label>
                  <input
                    type="text"
                    id="company"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="e.g., Google, Microsoft"
                    className="input-google"
                    disabled={isGenerating}
                    style={{ fontFamily: 'Google Sans, sans-serif' }}
                  />
                </div>
                <div>
                  <label htmlFor="role" style={{ 
                    display: 'block',
                    fontFamily: 'Google Sans, sans-serif',
                    fontSize: '0.95rem',
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}>
                    Role
                  </label>
                  <input
                    type="text"
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="e.g., Software Engineer Intern"
                    className="input-google"
                    disabled={isGenerating}
                    style={{ fontFamily: 'Google Sans, sans-serif' }}
                  />
                </div>
              </div>

              {/* Job Description */}
              <div style={{ marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label htmlFor="jdText" style={{ 
                    fontFamily: 'Google Sans, sans-serif',
                    fontSize: '0.95rem',
                    fontWeight: 500,
                    color: 'var(--text-primary)'
                  }}>
                    Job Description
                  </label>
                  <button
                    type="button"
                    onClick={handlePasteSample}
                    disabled={isGenerating}
                    style={{
                      fontFamily: 'Google Sans, sans-serif',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: 'var(--google-blue)',
                      background: 'none',
                      border: 'none',
                      cursor: isGenerating ? 'not-allowed' : 'pointer',
                      opacity: isGenerating ? 0.5 : 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <span className="material-icons" style={{ fontSize: '18px' }}>content_paste</span>
                    Paste Sample JD
                  </button>
                </div>
                <textarea
                  id="jdText"
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste the complete job description here..."
                  rows={12}
                  className="textarea-google"
                  disabled={isGenerating}
                  style={{ fontFamily: 'Google Sans, sans-serif' }}
                />
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '8px', fontFamily: 'Google Sans, sans-serif' }}>
                  {jdText.length} characters
                </p>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isGenerating}
                className="btn-google btn-google-primary"
                style={{ 
                  width: '100%',
                  opacity: isGenerating ? 0.6 : 1, 
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                  fontSize: '1.1rem',
                  padding: '16px'
                }}
              >
                <span className="material-icons" style={{ fontSize: '24px' }}>
                  {isGenerating ? 'hourglass_empty' : 'auto_awesome'}
                </span>
                {isGenerating ? 'Generating...' : 'Generate Resume'}
              </button>
            </form>
          </div>
        </div>
      </main>

      {/* Profile Completion Warning Modal */}
      {showWarning && (
        <div onClick={() => setShowWarning(false)} style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div onClick={(e) => e.stopPropagation()} style={{
            background: 'white',
            borderRadius: '8px',
            padding: '32px',
            maxWidth: '500px',
            margin: '20px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '20px' }}>
              <div style={{ width: '48px', height: '48px', background: '#ea4335', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span className="material-icons" style={{ color: 'white', fontSize: '28px' }}>warning</span>
              </div>
              <div>
                <h3 style={{ fontFamily: "'Product Sans', sans-serif", fontSize: '20px', marginBottom: '8px', color: 'var(--text-primary)' }}>
                  Profile Incomplete
                </h3>
                <p style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  Your profile is only {profileCompletion}% complete. We need at least 70% to generate quality resumes.
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowWarning(false)} style={{ padding: '9px 24px', background: 'white', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', borderRadius: '4px', fontFamily: "'Google Sans', sans-serif", fontSize: '14px', fontWeight: 500, cursor: 'pointer' }}>
                Cancel
              </button>
              <button onClick={() => router.push('/profile')} style={{ padding: '9px 24px', background: '#4285f4', color: 'white', border: 'none', borderRadius: '4px', fontFamily: "'Google Sans', sans-serif", fontSize: '14px', fontWeight: 500, cursor: 'pointer' }}>
                Update Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
