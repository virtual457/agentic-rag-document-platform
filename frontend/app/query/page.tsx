'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Citation = { source_id: string; filename?: string; chunk_index: number; snippet?: string; reason?: string };

export default function QueryPage() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading } = useAuth();
  const [query, setQuery] = useState('');
  const [triggerActions, setTriggerActions] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [running, setRunning] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [mode, setMode] = useState<'pipeline' | 'agent'>('pipeline');

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push('/login');
  }, [isAuthenticated, isLoading, router]);

  function reset() { setEvents([]); setAnswer(null); setCitations([]); setPending(null); }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || !token) return;
    reset(); setRunning(true);

    if (mode === 'pipeline') {
      const url = `${API}/api/query/stream?query=${encodeURIComponent(query)}&token=${encodeURIComponent(token)}&trigger_actions=${triggerActions}`;
      const es = new EventSource(url);
      const handler = (evt: MessageEvent) => {
        try {
          const data = JSON.parse(evt.data);
          setEvents((cur) => [...cur, data]);
          if (data.type === 'done' || data.node === 'done') {
            setAnswer(String(data.answer || ''));
            setCitations(data.citations || []);
            setRunning(false);
            es.close();
          }
        } catch {}
      };
      es.onmessage = handler;
      ['ingest_started', 'retrieval_complete', 'generation_complete', 'eval_round', 'validation_complete', 'actions_completed', 'done', 'route_decided', 'finalize_forced'].forEach((t) =>
        es.addEventListener(t, handler as EventListener),
      );
      es.onerror = () => { setRunning(false); es.close(); };
    } else {
      const wsUrl = API.replace(/^http/, 'ws') + `/api/agent/ws?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => ws.send(JSON.stringify({ type: 'query', query }));
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'question_prompt') setPending(msg.question);
          else if (msg.type === 'final') { setAnswer(msg.answer); setCitations(msg.citations || []); setRunning(false); ws.close(); }
          else setEvents((cur) => [...cur, msg]);
        } catch {}
      };
      ws.onerror = () => setRunning(false);
    }
  }

  function answerQuestion(a: string) {
    wsRef.current?.send(JSON.stringify({ type: 'user_answer', answer: a }));
    setPending(null);
  }

  return (
    <main style={{ maxWidth: 960, margin: '0 auto', padding: 24, color: '#e5e7eb' }}>
      <Link href="/dashboard" style={{ color: '#93c5fd', fontSize: 12, textDecoration: 'none' }}>← Dashboard</Link>
      <h1 style={{ fontSize: 28, margin: '12px 0 16px' }}>Ask a question</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <ModeButton active={mode === 'pipeline'} onClick={() => setMode('pipeline')}>Pipeline (SSE)</ModeButton>
        <ModeButton active={mode === 'agent'} onClick={() => setMode('agent')}>Agent (WebSocket)</ModeButton>
      </div>

      <form onSubmit={submit} style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. What causes CUDA OOM under burst inference?" style={{ flex: 1, padding: 10, background: '#020617', border: '1px solid #1f2937', borderRadius: 6, color: '#e5e7eb' }} />
        <button type="submit" disabled={running || !query.trim()} style={{ background: running ? '#334155' : '#2563eb', color: 'white', padding: '10px 20px', borderRadius: 6, border: 'none', cursor: running ? 'not-allowed' : 'pointer' }}>
          {running ? 'Working...' : 'Ask'}
        </button>
      </form>

      <label style={{ fontSize: 13, opacity: 0.8 }}>
        <input type="checkbox" checked={triggerActions} onChange={(e) => setTriggerActions(e.target.checked)} /> Allow Action Agent (Jira, Slack, ServiceNow)
      </label>

      {events.length > 0 && (
        <section style={{ marginTop: 24, padding: 16, background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Pipeline</div>
          <ul style={{ fontSize: 13, opacity: 0.85, listStyle: 'none', padding: 0, margin: 0 }}>
            {events.map((e, i) => <li key={i} style={{ padding: '2px 0' }}>• {describe(e)}</li>)}
          </ul>
        </section>
      )}

      {answer && (
        <section style={{ marginTop: 24, padding: 20, background: '#0b1220', border: '1px solid #1f2937', borderRadius: 8 }}>
          <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8 }}>Answer</div>
          <div style={{ whiteSpace: 'pre-wrap' }}>{answer}</div>
          {citations.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8 }}>Citations</div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {citations.map((c, i) => (
                  <li key={i} style={{ padding: 8, background: '#020617', border: '1px solid #1f2937', borderRadius: 6, marginBottom: 6, fontSize: 13 }}>
                    <div style={{ fontWeight: 500 }}>{c.filename || c.source_id} #{c.chunk_index}</div>
                    {c.reason && <div style={{ opacity: 0.7 }}>{c.reason}</div>}
                    {c.snippet && <div style={{ opacity: 0.6, marginTop: 4 }}>{c.snippet}</div>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {pending && <QuestionModal question={pending} onAnswer={answerQuestion} />}
    </main>
  );
}

function ModeButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} style={{ padding: '6px 14px', borderRadius: 6, border: active ? 'none' : '1px solid #374151', background: active ? '#2563eb' : 'transparent', color: '#e5e7eb', cursor: 'pointer' }}>
      {children}
    </button>
  );
}

function describe(e: any): string {
  const t = e.type || e.node;
  if (t === 'route_decided') return `Route: ${e.route}`;
  if (t === 'retrieval_complete') return `Retrieved ${e.hits} chunks`;
  if (t === 'generation_complete') return 'Generation complete';
  if (t === 'eval_round') return `Eval round ${e.round}: ${e.score}/100 ${e.passed ? '✓' : '↻'}`;
  if (t === 'validation_complete') return `Validation: ${e.passed ? 'supported' : 'gaps found'}`;
  if (t === 'actions_completed') return `Actions taken: ${e.count}`;
  if (t === 'done') return 'Done';
  return t || JSON.stringify(e);
}

function QuestionModal({ question, onAnswer }: { question: string; onAnswer: (a: string) => void }) {
  const [v, setV] = useState('');
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
      <div style={{ maxWidth: 520, width: '100%', padding: 24, background: '#0b1220', border: '1px solid #1f2937', borderRadius: 12, margin: 16 }}>
        <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 4 }}>Agent is asking</div>
        <div style={{ fontSize: 16, marginBottom: 16 }}>{question}</div>
        <textarea value={v} onChange={(e) => setV(e.target.value)} rows={3} style={{ width: '100%', padding: 10, background: '#020617', color: '#e5e7eb', border: '1px solid #1f2937', borderRadius: 6 }} />
        <div style={{ marginTop: 12, textAlign: 'right' }}>
          <button onClick={() => onAnswer(v)} style={{ background: '#2563eb', color: 'white', padding: '8px 16px', borderRadius: 6, border: 'none', cursor: 'pointer' }}>Send</button>
        </div>
      </div>
    </div>
  );
}
