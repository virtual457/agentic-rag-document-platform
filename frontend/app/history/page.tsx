'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Row = {
  query: string;
  answer: string;
  final_score: number;
  created_at: string;
  citations?: any[];
  route?: string;
};

export default function HistoryPage() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading } = useAuth();
  const [rows, setRows] = useState<Row[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/login');
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/query/history`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setRows)
      .catch((e) => setErr(String(e)));
  }, [token]);

  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: 24, color: '#e5e7eb' }}>
      <Link href="/dashboard" style={{ color: '#93c5fd', fontSize: 12, textDecoration: 'none' }}>← Dashboard</Link>
      <h1 style={{ fontSize: 28, margin: '12px 0 24px' }}>Query history</h1>
      {err && <div style={{ color: '#f87171' }}>{err}</div>}
      {rows.length === 0 && <div style={{ opacity: 0.6 }}>No queries yet.</div>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {rows.map((r, i) => (
          <div key={i} style={{ padding: 16, background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8 }}>
            <div style={{ fontSize: 12, opacity: 0.6 }}>{new Date(r.created_at).toLocaleString()} · score {r.final_score ?? '—'} · route {r.route ?? '—'}</div>
            <div style={{ fontWeight: 600, margin: '4px 0' }}>{r.query}</div>
            <div style={{ fontSize: 14, opacity: 0.9, whiteSpace: 'pre-wrap' }}>{r.answer}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
