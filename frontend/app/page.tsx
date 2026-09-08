'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (isLoading) return
    router.push(isAuthenticated ? '/dashboard' : '/login')
  }, [isAuthenticated, isLoading, router])

  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0b1220',
        color: '#e5e7eb',
        padding: '48px 24px',
        textAlign: 'center',
      }}
    >
      <h1
        style={{
          fontSize: 'clamp(2rem, 6vw, 3.5rem)',
          fontWeight: 700,
          letterSpacing: '-0.02em',
          margin: 0,
        }}
      >
        Document Intelligence Platform
      </h1>
      <p
        style={{
          maxWidth: 640,
          margin: '20px 0 32px',
          fontSize: '1.05rem',
          lineHeight: 1.55,
          color: '#94a3b8',
        }}
      >
        Agentic RAG over your enterprise documents. Multi-agent orchestration,
        hybrid retrieval, and grounded answers with tool-calling.
      </p>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link
          href="/register"
          style={{
            padding: '10px 22px',
            borderRadius: 8,
            background: '#2563eb',
            color: 'white',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Get Started
        </Link>
        <Link
          href="/login"
          style={{
            padding: '10px 22px',
            borderRadius: 8,
            border: '1px solid #374151',
            color: '#e5e7eb',
            textDecoration: 'none',
          }}
        >
          Sign in
        </Link>
      </div>
    </main>
  )
}
