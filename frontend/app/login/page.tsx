'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      login(data.access_token, data.user);
      router.push('/dashboard');
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0b1220',
        color: '#e5e7eb',
        padding: 24,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 420,
          padding: 32,
          background: '#111827',
          border: '1px solid #1f2937',
          borderRadius: 12,
        }}
      >
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Sign in</h1>
        <p style={{ color: '#94a3b8', margin: '6px 0 20px', fontSize: 14 }}>
          Continue to Document Intelligence Platform
        </p>
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            type="text"
            placeholder="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={inputStyle}
          />
          {error && <div style={{ color: '#f87171', fontSize: 13 }}>{error}</div>}
          <button
            type="submit"
            disabled={busy}
            style={{
              padding: '10px 18px',
              borderRadius: 8,
              background: busy ? '#334155' : '#2563eb',
              color: 'white',
              border: 'none',
              cursor: busy ? 'not-allowed' : 'pointer',
              fontWeight: 600,
            }}
          >
            {busy ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p style={{ marginTop: 16, fontSize: 13, color: '#94a3b8' }}>
          No account?{' '}
          <Link href="/register" style={{ color: '#93c5fd' }}>
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}

const inputStyle: React.CSSProperties = {
  padding: 10,
  background: '#020617',
  border: '1px solid #1f2937',
  borderRadius: 6,
  color: '#e5e7eb',
  outline: 'none',
};
