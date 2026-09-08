'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [form, setForm] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (form.password !== form.confirmPassword) return setError('Passwords do not match');
    if (form.password.length < 6) return setError('Password must be at least 6 characters');
    setBusy(true);
    try {
      const { confirmPassword: _, ...payload } = form;
      const r = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
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
          maxWidth: 440,
          padding: 32,
          background: '#111827',
          border: '1px solid #1f2937',
          borderRadius: 12,
        }}
      >
        <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>Create your account</h1>
        <p style={{ color: '#94a3b8', margin: '6px 0 20px', fontSize: 14 }}>
          One account for Document Intelligence Platform
        </p>
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input
            name="full_name"
            placeholder="full name"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            required
            style={inputStyle}
          />
          <input
            name="username"
            placeholder="username"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
            minLength={3}
            maxLength={50}
            style={inputStyle}
          />
          <input
            name="email"
            type="email"
            placeholder="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
            style={inputStyle}
          />
          <input
            name="password"
            type="password"
            placeholder="password (min 6 chars)"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            minLength={6}
            style={inputStyle}
          />
          <input
            name="confirmPassword"
            type="password"
            placeholder="confirm password"
            value={form.confirmPassword}
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
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
              marginTop: 8,
            }}
          >
            {busy ? 'Creating...' : 'Create account'}
          </button>
        </form>
        <p style={{ marginTop: 16, fontSize: 13, color: '#94a3b8' }}>
          Have an account?{' '}
          <Link href="/login" style={{ color: '#93c5fd' }}>
            Sign in
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
