'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await authAPI.login(formData);
      login(response.access_token, response.user);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-white)',
      padding: '20px'
    }}>
      {/* Google-Style Login Card */}
      <div style={{
        width: '100%',
        maxWidth: '450px',
        background: 'white',
        border: '1px solid var(--border-light)',
        borderRadius: '8px',
        padding: '48px 40px 36px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1), 0 8px 16px rgba(0,0,0,0.1)'
      }}>
        {/* Google Logo + Title */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          {/* LMARO Logo - Solid Color */}
          <div style={{
            display: 'inline-block',
            marginBottom: '16px'
          }}>
            <span style={{ 
              fontFamily: "'Product Sans', sans-serif",
              fontSize: '2.5rem',
              fontWeight: 400,
              color: 'var(--text-primary)'
            }}>LMARO</span>
          </div>
          
          <h1 style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '24px',
            fontWeight: 400,
            color: 'var(--text-primary)',
            marginBottom: '8px'
          }}>
            Sign in
          </h1>
          <p style={{
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '16px',
            color: 'var(--text-secondary)'
          }}>
            to continue to LMARO
          </p>
        </div>

        {/* Error Message - Google Style */}
        {error && (
          <div style={{
            marginBottom: '16px',
            padding: '12px 16px',
            background: '#fce8e6',
            border: '1px solid #f9dedc',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <span className="material-icons" style={{ 
              color: '#d93025',
              fontSize: '20px'
            }}>error_outline</span>
            <span style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: '#d93025',
              flex: 1
            }}>
              {error}
            </span>
          </div>
        )}

        {/* Login Form - Google Style */}
        <form onSubmit={handleSubmit}>
          {/* Username Input */}
          <div style={{ marginBottom: '24px' }}>
            <label htmlFor="username" style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--text-primary)',
              marginBottom: '8px',
              display: 'block',
              fontWeight: 500
            }}>
              Username
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="Enter your username"
              style={{
                width: '100%',
                padding: '13px 15px',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '16px',
                border: '1px solid var(--border-light)',
                borderRadius: '4px',
                outline: 'none',
                transition: 'all 0.2s ease',
                background: 'transparent'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = 'var(--google-blue)';
                e.target.style.boxShadow = '0 1px 1px 0 rgba(66,133,244,.45), 0 1px 3px 1px rgba(66,133,244,.3)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'var(--border-light)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          {/* Password Input */}
          <div style={{ marginBottom: '16px' }}>
            <label htmlFor="password" style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--text-primary)',
              marginBottom: '8px',
              display: 'block',
              fontWeight: 500
            }}>
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
              style={{
                width: '100%',
                padding: '13px 15px',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '16px',
                border: '1px solid var(--border-light)',
                borderRadius: '4px',
                outline: 'none',
                transition: 'all 0.2s ease',
                background: 'transparent'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = 'var(--google-blue)';
                e.target.style.boxShadow = '0 1px 1px 0 rgba(66,133,244,.45), 0 1px 3px 1px rgba(66,133,244,.3)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = 'var(--border-light)';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          {/* Forgot Password Link */}
          <div style={{ marginBottom: '24px' }}>
            <a href="#" style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '14px',
              color: 'var(--google-blue)',
              textDecoration: 'none',
              fontWeight: 500
            }}>
              Forgot password?
            </a>
          </div>

          {/* Action Buttons Row */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '12px',
            marginTop: '32px'
          }}>
            {/* Create Account Link */}
            <Link href="/register">
              <button
                type="button"
                style={{
                  padding: '9px 24px',
                  background: 'white',
                  color: 'var(--google-blue)',
                  border: 'none',
                  borderRadius: '4px',
                  fontFamily: "'Google Sans', sans-serif",
                  fontSize: '14px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(66,133,244,.04)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'white';
                }}
              >
                Create account
              </button>
            </Link>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={isLoading}
              style={{
                padding: '9px 24px',
                background: isLoading ? '#ccc' : 'var(--google-blue)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                fontWeight: 500,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                minWidth: '90px'
              }}
              onMouseEnter={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.background = '#1967d2';
                  e.currentTarget.style.boxShadow = '0 1px 2px 0 rgba(66,133,244,.3), 0 1px 3px 1px rgba(66,133,244,.15)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.background = 'var(--google-blue)';
                  e.currentTarget.style.boxShadow = 'none';
                }
              }}
            >
              {isLoading ? 'Signing in...' : 'Next'}
            </button>
          </div>
        </form>
      </div>

      {/* Language Selector Footer - Google Style */}
      <div style={{
        position: 'fixed',
        bottom: '0',
        left: '0',
        right: '0',
        padding: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: 'var(--text-secondary)',
        fontFamily: "'Google Sans', sans-serif"
      }}>
        <div style={{ display: 'flex', gap: '24px' }}>
          <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Help</a>
          <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Privacy</a>
          <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>Terms</a>
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span>English (United States)</span>
          <span className="material-icons" style={{ fontSize: '16px' }}>expand_more</span>
        </div>
      </div>
    </div>
  );
}
