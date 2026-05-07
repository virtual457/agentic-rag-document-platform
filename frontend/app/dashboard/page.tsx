'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ProfileCompletionWidget from '@/components/ProfileCompletionWidget';

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, logout, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

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
    );
  }

  if (!user || !token) {
    return null;
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-light)' }}>
      {/* Google-Style Navigation */}
      <nav style={{
        background: 'white',
        borderBottom: '1px solid var(--border-light)',
        padding: '0 24px',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '32px'
        }}>
          {/* Logo */}
          <Link href="/" style={{ textDecoration: 'none' }}>
            <div style={{ cursor: 'pointer' }}>
              <span style={{ fontFamily: "'Product Sans', sans-serif", fontSize: '22px', color: 'var(--text-primary)', fontWeight: 500 }}>LMARO</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <div style={{ display: 'flex', gap: '24px' }}>
            <Link href="/" style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              padding: '8px 12px',
              borderRadius: '4px',
              transition: 'background 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-light)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              Home
            </Link>
            <Link href="/generate" style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              padding: '8px 12px',
              borderRadius: '4px',
              transition: 'background 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-light)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              Generate
            </Link>
            <Link href="/profile" style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              padding: '8px 12px',
              borderRadius: '4px',
              transition: 'background 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-light)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              Update Profile
            </Link>
          </div>
        </div>

        {/* User Menu */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px'
        }}>
          {/* Profile Circle - Google Style */}
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: '#ea4335',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer'
          }}>
            {user.full_name?.charAt(0).toUpperCase()}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '48px 24px'
      }}>
        {/* Welcome Section - Google Style */}
        <div style={{
          background: 'white',
          borderRadius: '8px',
          border: '1px solid var(--border-light)',
          padding: '32px',
          marginBottom: '24px',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: '#4285f4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <span className="material-icons" style={{ color: 'white', fontSize: '28px' }}>person</span>
            </div>
            <div>
              <h1 style={{
                fontFamily: "'Product Sans', sans-serif",
                fontSize: '28px',
                color: 'var(--text-primary)',
                marginBottom: '4px'
              }}>
                Welcome back, {user.full_name?.split(' ')[0]}!
              </h1>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-secondary)'
              }}>
                {user.email}
              </p>
            </div>
          </div>
        </div>

        {/* Profile Completion Widget */}
        <ProfileCompletionWidget userId={user.user_id} token={token} />

        {/* Quick Actions Grid - Google Style */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          {/* Generate Resume Card */}
          <Link href="/generate" style={{ textDecoration: 'none' }}>
            <div className="card-google" style={{
              padding: '24px',
              cursor: 'pointer',
              height: '100%'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'var(--google-blue)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <span className="material-icons" style={{ color: 'white', fontSize: '24px' }}>
                  description
                </span>
              </div>
              <h3 style={{
                fontFamily: "'Product Sans', sans-serif",
                fontSize: '18px',
                color: 'var(--text-primary)',
                marginBottom: '8px'
              }}>
                Generate Resume
              </h3>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-secondary)',
                lineHeight: 1.5
              }}>
                Create a tailored resume from job description using AI
              </p>
            </div>
          </Link>

          {/* My Resumes Card */}
          <Link href="/resumes" style={{ textDecoration: 'none' }}>
            <div className="card-google" style={{
              padding: '24px',
              cursor: 'pointer',
              height: '100%'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'var(--google-red)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px'
              }}>
                <span className="material-icons" style={{ color: 'white', fontSize: '24px' }}>
                  folder
                </span>
              </div>
              <h3 style={{
                fontFamily: "'Product Sans', sans-serif",
                fontSize: '18px',
                color: 'var(--text-primary)',
                marginBottom: '8px'
              }}>
                My Resumes
              </h3>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-secondary)',
                lineHeight: 1.5
              }}>
                View and manage your generated resumes
              </p>
            </div>
          </Link>

          {/* Logout Card */}
          <div className="card-google" style={{
            padding: '24px',
            cursor: 'pointer',
            height: '100%'
          }}
          onClick={handleLogout}
          >
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'var(--google-green)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px'
            }}>
              <span className="material-icons" style={{ color: 'white', fontSize: '24px' }}>
                logout
              </span>
            </div>
            <h3 style={{
              fontFamily: "'Product Sans', sans-serif",
              fontSize: '18px',
              color: 'var(--text-primary)',
              marginBottom: '8px'
            }}>
              Logout
            </h3>
            <p style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--text-secondary)',
              lineHeight: 1.5
            }}>
              Sign out of your account
            </p>
          </div>
        </div>

        {/* Account Info Section */}
        <div style={{
          background: 'white',
          borderRadius: '8px',
          border: '1px solid var(--border-light)',
          padding: '32px',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
        }}>
          <h2 style={{
            fontFamily: "'Product Sans', sans-serif",
            fontSize: '20px',
            color: 'var(--text-primary)',
            marginBottom: '24px',
            paddingBottom: '16px',
            borderBottom: '1px solid var(--border-light)'
          }}>
            Account Information
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '24px'
          }}>
            <div>
              <label style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '12px',
                color: 'var(--text-secondary)',
                marginBottom: '8px',
                display: 'block',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                User ID
              </label>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-primary)',
                wordBreak: 'break-all'
              }}>
                {user.user_id}
              </p>
            </div>

            <div>
              <label style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '12px',
                color: 'var(--text-secondary)',
                marginBottom: '8px',
                display: 'block',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Username
              </label>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-primary)'
              }}>
                {user.username}
              </p>
            </div>

            <div>
              <label style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '12px',
                color: 'var(--text-secondary)',
                marginBottom: '8px',
                display: 'block',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Email
              </label>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-primary)'
              }}>
                {user.email}
              </p>
            </div>

            <div>
              <label style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '12px',
                color: 'var(--text-secondary)',
                marginBottom: '8px',
                display: 'block',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Full Name
              </label>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-primary)'
              }}>
                {user.full_name}
              </p>
            </div>

            <div>
              <label style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '12px',
                color: 'var(--text-secondary)',
                marginBottom: '8px',
                display: 'block',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Status
              </label>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 12px',
                background: '#e8f5e9',
                borderRadius: '16px'
              }}>
                <span className="material-icons" style={{ 
                  fontSize: '16px',
                  color: 'var(--google-green)'
                }}>check_circle</span>
                <span style={{
                  fontFamily: "'Google Sans', sans-serif",
                  fontSize: '13px',
                  color: 'var(--google-green)',
                  fontWeight: 500
                }}>
                  Active
                </span>
              </div>
            </div>

            <div>
              <label style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '12px',
                color: 'var(--text-secondary)',
                marginBottom: '8px',
                display: 'block',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Member Since
              </label>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-primary)'
              }}>
                {new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          </div>
        </div>

        {/* ChromaDB Info Banner */}
        <div style={{
          background: '#e8f0fe',
          borderLeft: '4px solid var(--google-blue)',
          padding: '16px 20px',
          marginTop: '24px',
          borderRadius: '4px'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
            <span className="material-icons" style={{ color: 'var(--google-blue)', fontSize: '20px' }}>
              storage
            </span>
            <div>
              <p style={{
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-primary)',
                marginBottom: '4px',
                fontWeight: 500
              }}>
                Your Personal Vector Database
              </p>
              <p style={{
                fontFamily: 'monospace',
                fontSize: '12px',
                color: 'var(--text-secondary)'
              }}>
                chromadb_store/user_{user.user_id}/
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
