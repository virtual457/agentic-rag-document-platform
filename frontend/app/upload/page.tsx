'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Source = { source_id: string; filename: string; source_type: string; chunk_count: number; created_at: string };

export default function UploadPage() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/login');
  }, [isAuthenticated, isLoading, router]);

  async function refresh() {
    if (!token) return;
    const r = await fetch(`${API}/api/upload/sources`, { headers: { Authorization: `Bearer ${token}` } });
    if (r.ok) setSources(await r.json());
  }
  useEffect(() => { refresh(); }, [token]);

  async function submitFile(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !token) return;
    setBusy(true); setErr(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await fetch(`${API}/api/upload/file`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd });
      if (!r.ok) throw new Error(await r.text());
      setFile(null); await refresh();
    } catch (e) { setErr(String(e)); }
    finally { setBusy(false); }
  }

  async function submitUrl(e: React.FormEvent) {
    e.preventDefault();
    if (!url || !token) return;
    setBusy(true); setErr(null);
    try {
      const r = await fetch(`${API}/api/upload/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ url }),
      });
      if (!r.ok) throw new Error(await r.text());
      setUrl(''); await refresh();
    } catch (e) { setErr(String(e)); }
    finally { setBusy(false); }
  }

  async function remove(id: string) {
    if (!token) return;
    await fetch(`${API}/api/upload/sources/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    await refresh();
  }

  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: 24, color: '#e5e7eb' }}>
      <Link href="/dashboard" style={{ color: '#93c5fd', fontSize: 12, textDecoration: 'none' }}>← Dashboard</Link>
      <h1 style={{ fontSize: 28, margin: '12px 0 24px' }}>Upload documents</h1>

      <section style={{ padding: 20, background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8, marginBottom: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>File (PDF, DOCX, HTML, MD, TXT, LOG)</div>
        <form onSubmit={submitFile} style={{ display: 'flex', gap: 8 }}>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button type="submit" disabled={!file || busy} style={btn(!file || busy)}>{busy ? 'Ingesting...' : 'Ingest'}</button>
        </form>
      </section>

      <section style={{ padding: 20, background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8, marginBottom: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>URL</div>
        <form onSubmit={submitUrl} style={{ display: 'flex', gap: 8 }}>
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/doc" style={{ flex: 1, padding: 8, background: '#020617', border: '1px solid #1f2937', borderRadius: 6, color: '#e5e7eb' }} />
          <button type="submit" disabled={!url || busy} style={btn(!url || busy)}>{busy ? 'Fetching...' : 'Ingest URL'}</button>
        </form>
      </section>

      {err && <div style={{ color: '#f87171', marginBottom: 16 }}>{err}</div>}

      <h2 style={{ fontSize: 18, margin: '24px 0 8px' }}>Ingested sources</h2>
      <div style={{ border: '1px solid #1f2937', borderRadius: 8, overflow: 'hidden' }}>
        {sources.length === 0 && <div style={{ padding: 16, opacity: 0.6 }}>No sources yet.</div>}
        {sources.map((s) => (
          <div key={s.source_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 12, borderBottom: '1px solid #1f2937' }}>
            <div>
              <div style={{ fontWeight: 500 }}>{s.filename}</div>
              <div style={{ fontSize: 12, opacity: 0.6 }}>{s.source_type} · {s.chunk_count} chunks · {new Date(s.created_at).toLocaleString()}</div>
            </div>
            <button onClick={() => remove(s.source_id)} style={{ background: 'transparent', border: '1px solid #7f1d1d', color: '#fca5a5', padding: '6px 12px', borderRadius: 6, cursor: 'pointer' }}>Delete</button>
          </div>
        ))}
      </div>
    </main>
  );
}

function btn(disabled: boolean): React.CSSProperties {
  return { background: disabled ? '#334155' : '#2563eb', color: 'white', padding: '8px 16px', borderRadius: 6, border: 'none', cursor: disabled ? 'not-allowed' : 'pointer' };
}
