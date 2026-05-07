'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import EntityCard from '@/components/EntityCard';
import { profileBuilderAPI } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ExtractedEntity {
  id: string;
  entity_type: string;
  data: Record<string, any>;
  confidence: number;
  needs_clarification: boolean;
  clarification_question?: string;
  field_to_update?: string;
}

interface AgentResponse {
  session_id: string;
  message: string;
  action: string;
  current_entity?: ExtractedEntity;
  pending_entities: ExtractedEntity[];
  pending_count: number;
  confirmed_count: number;
  saved_count: number;
  waiting_for_user: boolean;
  is_complete: boolean;
  question_for_entity_id?: string;
  question_for_field?: string;
}

export default function ProfileBuilderPage() {
  const router = useRouter();
  const { user, token, isAuthenticated, isLoading } = useAuth();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // All pending entities from backend
  const [pendingEntities, setPendingEntities] = useState<ExtractedEntity[]>([]);
  // Current entity being worked on
  const [currentEntity, setCurrentEntity] = useState<ExtractedEntity | null>(null);
  
  const [stats, setStats] = useState({ pending: 0, confirmed: 0, saved: 0 });
  const [profileCompletion, setProfileCompletion] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: `Hi! I'm your Profile Builder assistant.\n\nPaste your resume, describe your work experience, or tell me about your projects. I'll extract the information and you can confirm each item.`,
        timestamp: new Date()
      }]);
    }
  }, []);

  // Fetch profile completion when user is available
  useEffect(() => {
    const fetchProfileCompletion = async () => {
      if (user && token) {
        try {
          const response = await fetch(`http://localhost:8000/api/profile/completion`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (response.ok) {
            const data = await response.json();
            setProfileCompletion(data.percentage || 0);  // Fixed: use 'percentage' not 'completion_percentage'
          }
        } catch (error) {
          console.error('Failed to fetch profile completion:', error);
        }
      }
    };

    fetchProfileCompletion();
  }, [user, token, stats.saved]); // Re-fetch when items are saved

  const handleResponse = (response: AgentResponse) => {
    setSessionId(response.session_id);
    setStats({
      pending: response.pending_count,
      confirmed: response.confirmed_count,
      saved: response.saved_count
    });
    
    // Update pending entities from backend
    setPendingEntities(response.pending_entities || []);
    
    // Update current entity (this has the LATEST data)
    setCurrentEntity(response.current_entity || null);
    
    // Add assistant message
    if (response.message) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date()
      }]);
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsProcessing(true);

    try {
      const response: AgentResponse = await profileBuilderAPI.chat(
        token!,
        inputText,
        sessionId || undefined
      );
      handleResponse(response);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleEntityAction = async (action: 'confirm' | 'edit' | 'skip', editedData?: Record<string, any>) => {
    if (!currentEntity || !sessionId) return;

    setIsProcessing(true);

    try {
      const response: AgentResponse = await profileBuilderAPI.confirmEntity(
        token!,
        sessionId,
        {
          entity_id: currentEntity.id,
          action,
          edited_data: editedData
        }
      );
      handleResponse(response);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="google-loader">
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
          <div className="loader-dot"></div>
        </div>
      </div>
    );
  }

  if (!user || !token) return null;

  // Should we show the entity card?
  const showEntityCard = currentEntity && !currentEntity.needs_clarification;

  return (
    <div style={{ height: '100vh', background: 'var(--bg-light)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Navigation */}
      <nav style={{
        background: 'white',
        borderBottom: '1px solid var(--border-light)',
        padding: '0 24px',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <Link href="/dashboard" style={{ textDecoration: 'none' }}>
            <span style={{ fontFamily: "'Product Sans', sans-serif", fontSize: '22px', color: 'var(--text-primary)', fontWeight: 500 }}>LMARO</span>
          </Link>
          <span style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px', color: 'var(--text-secondary)' }}>
            Profile Builder
          </span>
        </div>

        {/* Stats */}
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="material-icons" style={{ fontSize: '18px', color: 'var(--google-yellow)' }}>pending</span>
            <span style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px' }}>{stats.pending} pending</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="material-icons" style={{ fontSize: '18px', color: 'var(--google-blue)' }}>check_circle</span>
            <span style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px' }}>{stats.confirmed} confirmed</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="material-icons" style={{ fontSize: '18px', color: 'var(--google-green)' }}>save</span>
            <span style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px' }}>{stats.saved} saved</span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', maxWidth: '1400px', margin: '0 auto', width: '100%', padding: '24px', gap: '24px', overflow: 'hidden', minHeight: 0 }}>
        
        {/* Chat Area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingBottom: '16px', paddingRight: '8px' }}>
            {messages.map((msg) => (
              <div key={msg.id} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{
                  maxWidth: '75%',
                  padding: '12px 16px',
                  borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                  background: msg.role === 'user' ? 'var(--google-blue)' : 'white',
                  color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                  fontFamily: "'Google Sans', sans-serif",
                  fontSize: '14px',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-wrap'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Show entity card in chat flow */}
            {showEntityCard && currentEntity && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '8px' }}>
                <div style={{ maxWidth: '85%', width: '100%' }}>
                  <EntityCard
                    entity={currentEntity}
                    onConfirm={() => handleEntityAction('confirm')}
                    onEdit={(data) => handleEntityAction('edit', data)}
                    onSkip={() => handleEntityAction('skip')}
                    isProcessing={isProcessing}
                  />
                </div>
              </div>
            )}

            {isProcessing && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  padding: '12px 16px',
                  borderRadius: '18px',
                  background: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Thinking...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{
            background: 'white',
            borderRadius: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'flex-end',
            gap: '12px',
            flexShrink: 0
          }}>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste resume, describe experience, or answer questions..."
              disabled={isProcessing}
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                resize: 'none',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                lineHeight: 1.5,
                minHeight: '24px',
                maxHeight: '120px',
                padding: '8px 0'
              }}
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isProcessing}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                border: 'none',
                background: inputText.trim() && !isProcessing ? 'var(--google-blue)' : '#e0e0e0',
                color: 'white',
                cursor: inputText.trim() && !isProcessing ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <span className="material-icons" style={{ fontSize: '20px' }}>send</span>
            </button>
          </div>
        </div>

        {/* Side Panel - Pending Items */}
        <div style={{ width: '320px', flexShrink: 0, display: 'flex', flexDirection: 'column', minHeight: 0, gap: '16px' }}>
          {pendingEntities.length > 0 ? (
            <div style={{
              background: 'white',
              borderRadius: '12px',
              padding: '20px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
              flex: 1
            }}>
              <h3 style={{ 
                fontFamily: "'Product Sans', sans-serif", 
                fontSize: '16px', 
                marginBottom: '16px',
                color: 'var(--text-primary)',
                flexShrink: 0
              }}>
                Queue ({pendingEntities.length})
              </h3>
              <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
                {pendingEntities.map((e, index) => (
                  <div key={e.id} style={{
                    padding: '12px',
                    borderRadius: '8px',
                    background: e.needs_clarification ? '#fff3e0' : '#e8f5e9',
                    marginBottom: '8px',
                    border: `1px solid ${e.needs_clarification ? '#ffcc80' : '#a5d6a7'}`,
                    opacity: index === 0 ? 1 : 0.7
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      {index === 0 && (
                        <span style={{
                          background: 'var(--google-blue)',
                          color: 'white',
                          fontSize: '10px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontWeight: 600
                        }}>
                          NEXT
                        </span>
                      )}
                      <span className="material-icons" style={{ 
                        fontSize: '16px', 
                        color: e.needs_clarification ? 'var(--google-yellow)' : 'var(--google-green)' 
                      }}>
                        {e.needs_clarification ? 'help' : 'check_circle'}
                      </span>
                      <span style={{ 
                        fontFamily: "'Google Sans', sans-serif", 
                        fontSize: '13px', 
                        fontWeight: 500,
                        textTransform: 'capitalize'
                      }}>
                        {e.entity_type.replace('_', ' ')}
                      </span>
                    </div>
                    <div style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {e.data.company || e.data.name || e.data.institution || 'Details pending...'}
                    </div>
                    {e.needs_clarification && (
                      <div style={{ 
                        marginTop: '8px', 
                        fontSize: '11px', 
                        color: '#e65100',
                        fontStyle: 'italic'
                      }}>
                        ⚠️ Needs clarification
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{
              background: 'white',
              borderRadius: '12px',
              padding: '32px 20px',
              textAlign: 'center',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              flex: 1
            }}>
              <span className="material-icons" style={{ fontSize: '48px', color: '#e0e0e0', marginBottom: '12px' }}>
                check_circle
              </span>
              <p style={{ fontFamily: "'Google Sans', sans-serif", fontSize: '14px', color: 'var(--text-secondary)' }}>
                All caught up!
              </p>
            </div>
          )}

          {/* Profile Status */}
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '16px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            flexShrink: 0
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <span className="material-icons" style={{ fontSize: '20px', color: 'var(--google-blue)' }}>
                account_circle
              </span>
              <h3 style={{ 
                fontFamily: "'Product Sans', sans-serif", 
                fontSize: '14px', 
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Profile Status
              </h3>
            </div>

            {/* Profile Completion Progress */}
            <div style={{ 
              marginBottom: '16px',
              paddingBottom: '16px',
              borderBottom: '1px solid var(--border-light)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '13px', 
                  fontWeight: 500,
                  color: 'var(--text-primary)' 
                }}>
                  Profile Completion
                </span>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '16px', 
                  fontWeight: 600,
                  color: profileCompletion >= 80 ? 'var(--google-green)' : profileCompletion >= 50 ? 'var(--google-yellow)' : 'var(--google-red)' 
                }}>
                  {Math.round(profileCompletion)}%
                </span>
              </div>
              
              {/* Progress Bar */}
              <div style={{ 
                width: '100%', 
                height: '8px', 
                background: '#e0e0e0', 
                borderRadius: '4px',
                overflow: 'hidden',
                position: 'relative'
              }}>
                <div style={{ 
                  width: `${profileCompletion}%`, 
                  height: '100%', 
                  background: profileCompletion >= 80 
                    ? 'linear-gradient(90deg, var(--google-green) 0%, #00c853 100%)' 
                    : profileCompletion >= 50 
                    ? 'linear-gradient(90deg, var(--google-yellow) 0%, #ffc107 100%)' 
                    : 'linear-gradient(90deg, var(--google-red) 0%, #f44336 100%)',
                  transition: 'width 0.3s ease',
                  borderRadius: '4px'
                }} />
              </div>

              {/* Status Message */}
              <div style={{ marginTop: '6px' }}>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '11px', 
                  color: 'var(--text-secondary)',
                  fontStyle: 'italic'
                }}>
                  {profileCompletion >= 80 
                    ? '✓ Your profile looks great!' 
                    : profileCompletion >= 50 
                    ? 'Add more details to stand out' 
                    : 'Let\'s build your profile together'}
                </span>
              </div>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '13px', 
                  color: 'var(--text-secondary)' 
                }}>
                  In Queue
                </span>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '16px', 
                  fontWeight: 600,
                  color: 'var(--google-yellow)' 
                }}>
                  {stats.pending}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '13px', 
                  color: 'var(--text-secondary)' 
                }}>
                  Confirmed
                </span>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '16px', 
                  fontWeight: 600,
                  color: 'var(--google-blue)' 
                }}>
                  {stats.confirmed}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '13px', 
                  color: 'var(--text-secondary)' 
                }}>
                  Saved
                </span>
                <span style={{ 
                  fontFamily: "'Google Sans', sans-serif", 
                  fontSize: '16px', 
                  fontWeight: 600,
                  color: 'var(--google-green)' 
                }}>
                  {stats.saved}
                </span>
              </div>

              <div style={{ 
                marginTop: '8px', 
                paddingTop: '8px', 
                borderTop: '1px solid var(--border-light)' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ 
                    fontFamily: "'Google Sans', sans-serif", 
                    fontSize: '13px', 
                    fontWeight: 500,
                    color: 'var(--text-primary)' 
                  }}>
                    Total Items
                  </span>
                  <span style={{ 
                    fontFamily: "'Google Sans', sans-serif", 
                    fontSize: '18px', 
                    fontWeight: 600,
                    color: 'var(--text-primary)' 
                  }}>
                    {stats.pending + stats.confirmed + stats.saved}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
