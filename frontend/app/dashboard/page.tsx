'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

type Stats = { source_count: number; chunk_count: number; vector_backend: string; metadata_backend: string };

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, logout, isAuthenticated, isLoading } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/login');
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/admin/stats`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setStats)
      .catch((e) => setErr(String(e)));
  }, [token]);

  if (isLoading || !isAuthenticated) return null;

  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: 24, color: '#e5e7eb' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <div style={{ fontSize: 12, opacity: 0.6 }}>Signed in as</div>
          <div style={{ fontWeight: 600 }}>{user?.full_name || user?.username}</div>
        </div>
        <button
          onClick={() => {
            logout();
            router.push('/login');
          }}
          style={{ background: 'transparent', border: '1px solid #374151', color: '#e5e7eb', padding: '6px 14px', borderRadius: 6, cursor: 'pointer' }}
        >
          Sign out
        </button>
      </header>

      <h1 style={{ fontSize: 32, margin: '8px 0 24px' }}>Document Intelligence Platform</h1>

      {err && <div style={{ color: '#f87171', marginBottom: 16 }}>{err}</div>}

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 32 }}>
        <Card label="Sources" value={stats?.source_count ?? '—'} />
        <Card label="Chunks indexed" value={stats?.chunk_count ?? '—'} />
        <Card label="Vector backend" value={stats?.vector_backend ?? '—'} />
      </section>

      <nav style={{ display: 'flex', gap: 12 }}>
        <ActionLink href="/upload" label="Upload documents" primary />
        <ActionLink href="/query" label="Ask a question" />
        <ActionLink href="/history" label="History" />
      </nav>
    </main>
  );
}

function Card({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ padding: 20, border: '1px solid #1f2937', borderRadius: 8, background: '#0b1220' }}>
      <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

function ActionLink({ href, label, primary }: { href: string; label: string; primary?: boolean }) {
  const style = primary
    ? { background: '#2563eb', color: 'white' }
    : { background: 'transparent', border: '1px solid #374151', color: '#e5e7eb' };
  return (
    <Link href={href} style={{ ...style, padding: '10px 18px', borderRadius: 8, textDecoration: 'none' } as React.CSSProperties}>
      {label}
    </Link>
  );
}
