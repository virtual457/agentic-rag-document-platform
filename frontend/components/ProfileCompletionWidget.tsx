'use client';

import { useEffect, useState } from 'react';

interface ProfileCompletionProps {
  userId: string;
  token: string;
}

interface CompletionData {
  percentage: number;
  status: string;
  feedback: string;
  missing_sections: string[];
  strengths?: string[];
  next_steps?: string;
}

export default function ProfileCompletionWidget({ userId, token }: ProfileCompletionProps) {
  const [completion, setCompletion] = useState<CompletionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompletion();
  }, []);

  const fetchCompletion = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/profile/completion', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setCompletion(data);
    } catch (error) {
      console.error('Failed to fetch completion:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div className="google-loader" style={{ margin: '0 auto' }}>
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
        </div>
      </div>
    );
  }

  if (!completion) {
    return null;
  }

  const getColor = () => {
    if (completion.percentage >= 90) return 'var(--google-green)';
    if (completion.percentage >= 60) return 'var(--google-yellow)';
    return 'var(--google-red)';
  };

  const getStatusIcon = () => {
    if (completion.status === 'ready') return 'check_circle';
    if (completion.status === 'needs_improvement') return 'warning';
    return 'error';
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '8px',
      border: '1px solid var(--border-light)',
      padding: '24px',
      marginBottom: '24px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px'
      }}>
        <h3 style={{
          fontFamily: "'Product Sans', sans-serif",
          fontSize: '18px',
          color: 'var(--text-primary)',
          margin: 0
        }}>
          Profile Completion
        </h3>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span className="material-icons" style={{ 
            fontSize: '20px',
            color: getColor()
          }}>
            {getStatusIcon()}
          </span>
          <span style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '24px',
            fontWeight: 700,
            color: getColor()
          }}>
            {completion.percentage}%
          </span>
        </div>
      </div>

      {/* Progress Bar - Google Style */}
      <div style={{
        width: '100%',
        height: '8px',
        background: 'var(--bg-light)',
        borderRadius: '4px',
        overflow: 'hidden',
        marginBottom: '16px'
      }}>
        <div style={{
          width: `${completion.percentage}%`,
          height: '100%',
          background: getColor(),
          transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
        }}></div>
      </div>

      {/* Feedback */}
      <p style={{
        fontFamily: "'Google Sans', sans-serif",
        fontSize: '14px',
        color: 'var(--text-secondary)',
        lineHeight: 1.6,
        marginBottom: '16px'
      }}>
        {completion.feedback}
      </p>

      {/* Missing Sections */}
      {completion.missing_sections && completion.missing_sections.length > 0 && (
        <div style={{
          background: '#fef7e0',
          border: '1px solid #f9ab00',
          borderRadius: '4px',
          padding: '12px 16px',
          marginBottom: '12px'
        }}>
          <p style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '13px',
            color: '#9c6c00',
            margin: 0,
            marginBottom: '8px',
            fontWeight: 500
          }}>
            Missing Sections:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {completion.missing_sections.map((section, idx) => (
              <span key={idx} style={{
                padding: '4px 12px',
                background: 'white',
                borderRadius: '12px',
                fontSize: '12px',
                color: '#9c6c00',
                fontFamily: "'Google Sans', sans-serif",
                border: '1px solid #f9ab00'
              }}>
                {section}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Strengths */}
      {completion.strengths && completion.strengths.length > 0 && (
        <div style={{
          background: '#e8f5e9',
          border: '1px solid var(--google-green)',
          borderRadius: '4px',
          padding: '12px 16px',
          marginBottom: '12px'
        }}>
          <p style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '13px',
            color: 'var(--google-green)',
            margin: 0,
            marginBottom: '8px',
            fontWeight: 500
          }}>
            ✓ Complete Sections:
          </p>
          <ul style={{
            margin: 0,
            paddingLeft: '20px',
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '12px',
            color: '#137333'
          }}>
            {completion.strengths.map((strength, idx) => (
              <li key={idx}>{strength}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Next Steps */}
      {completion.next_steps && (
        <div style={{
          background: '#e8f0fe',
          borderLeft: '4px solid var(--google-blue)',
          padding: '12px 16px',
          borderRadius: '4px'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <span className="material-icons" style={{ 
              color: 'var(--google-blue)',
              fontSize: '20px'
            }}>
              lightbulb
            </span>
            <div>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '13px',
                color: '#1967d2',
                margin: 0,
                fontWeight: 500,
                marginBottom: '4px'
              }}>
                Next Steps:
              </p>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '13px',
                color: 'var(--text-secondary)',
                margin: 0,
                lineHeight: 1.5
              }}>
                {completion.next_steps}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
