'use client';

import { useState } from 'react';

interface ExtractedEntity {
  id: string;
  entity_type: string;
  data: Record<string, any>;
  confidence: number;
  needs_clarification: boolean;
  clarification_question?: string;
}

interface EntityCardProps {
  entity: ExtractedEntity;
  onConfirm: () => void;
  onEdit: (data: Record<string, any>) => void;
  onSkip: () => void;
  isProcessing: boolean;
}

const ENTITY_ICONS: Record<string, string> = {
  work_experience: 'work',
  project: 'code',
  education: 'school',
  skill: 'psychology',
  certification: 'verified',
  achievement: 'emoji_events',
  personal_info: 'person'
};

const ENTITY_COLORS: Record<string, string> = {
  work_experience: 'var(--google-blue)',
  project: 'var(--google-green)',
  education: 'var(--google-yellow)',
  skill: 'var(--google-red)',
  certification: '#9c27b0',
  achievement: '#ff9800',
  personal_info: '#607d8b'
};

const ENTITY_LABELS: Record<string, string> = {
  work_experience: 'Work Experience',
  project: 'Project',
  education: 'Education',
  skill: 'Skill',
  certification: 'Certification',
  achievement: 'Achievement',
  personal_info: 'Personal Info'
};

export default function EntityCard({ entity, onConfirm, onEdit, onSkip, isProcessing }: EntityCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState(entity.data);

  const icon = ENTITY_ICONS[entity.entity_type] || 'description';
  const color = ENTITY_COLORS[entity.entity_type] || 'var(--google-blue)';
  const label = ENTITY_LABELS[entity.entity_type] || entity.entity_type;

  const handleFieldChange = (key: string, value: any) => {
    setEditedData(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveEdit = () => {
    onEdit(editedData);
    setIsEditing(false);
  };

  const renderFieldValue = (key: string, value: any) => {
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value);
    }
    return String(value);
  };

  const renderEditField = (key: string, value: any) => {
    if (Array.isArray(value)) {
      return (
        <textarea
          value={value.join('\n')}
          onChange={(e) => handleFieldChange(key, e.target.value.split('\n').filter(v => v.trim()))}
          style={{
            width: '100%',
            padding: '8px',
            borderRadius: '4px',
            border: '1px solid var(--border-light)',
            fontFamily: "'Google Sans', sans-serif",
            fontSize: '13px',
            minHeight: '60px',
            resize: 'vertical'
          }}
        />
      );
    }
    return (
      <input
        type="text"
        value={String(value || '')}
        onChange={(e) => handleFieldChange(key, e.target.value)}
        style={{
          width: '100%',
          padding: '8px',
          borderRadius: '4px',
          border: '1px solid var(--border-light)',
          fontFamily: "'Google Sans', sans-serif",
          fontSize: '13px'
        }}
      />
    );
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      border: '1px solid var(--border-light)',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(135deg, ${color}15, ${color}05)`,
        padding: '16px',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <span className="material-icons" style={{ color: 'white', fontSize: '20px' }}>{icon}</span>
          </div>
          <div>
            <h3 style={{
              fontFamily: "'Product Sans', sans-serif",
              fontSize: '16px',
              color: 'var(--text-primary)',
              margin: 0
            }}>
              {label}
            </h3>
            <span style={{
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '12px',
              color: 'var(--text-secondary)'
            }}>
              {Math.round(entity.confidence * 100)}% confidence
            </span>
          </div>
        </div>
        
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            style={{
              padding: '6px 12px',
              borderRadius: '4px',
              border: '1px solid var(--border-light)',
              background: 'white',
              fontFamily: "'Google Sans', sans-serif",
              fontSize: '12px',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <span className="material-icons" style={{ fontSize: '14px' }}>edit</span>
            Edit
          </button>
        )}
      </div>

      {/* Content */}
      <div style={{ padding: '16px' }}>
        {isEditing ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {Object.entries(editedData).map(([key, value]) => (
              <div key={key}>
                <label style={{
                  display: 'block',
                  fontFamily: "'Google Sans', sans-serif",
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                  marginBottom: '4px',
                  textTransform: 'capitalize'
                }}>
                  {key.replace(/_/g, ' ')}
                </label>
                {renderEditField(key, value)}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Object.entries(entity.data).map(([key, value]) => (
              <div key={key} style={{ display: 'flex', gap: '8px' }}>
                <span style={{
                  fontFamily: "'Google Sans', sans-serif",
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  minWidth: '100px',
                  textTransform: 'capitalize'
                }}>
                  {key.replace(/_/g, ' ')}:
                </span>
                <span style={{
                  fontFamily: "'Google Sans', sans-serif",
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  flex: 1
                }}>
                  {renderFieldValue(key, value)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--border-light)',
        background: '#fafafa',
        display: 'flex',
        justifyContent: 'flex-end',
        gap: '8px'
      }}>
        {isEditing ? (
          <>
            <button
              onClick={() => {
                setEditedData(entity.data);
                setIsEditing(false);
              }}
              style={{
                padding: '8px 16px',
                borderRadius: '4px',
                border: '1px solid var(--border-light)',
                background: 'white',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-secondary)',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSaveEdit}
              disabled={isProcessing}
              style={{
                padding: '8px 16px',
                borderRadius: '4px',
                border: 'none',
                background: 'var(--google-blue)',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'white',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                opacity: isProcessing ? 0.7 : 1
              }}
            >
              Save & Confirm
            </button>
          </>
        ) : (
          <>
            <button
              onClick={onSkip}
              disabled={isProcessing}
              style={{
                padding: '8px 16px',
                borderRadius: '4px',
                border: '1px solid var(--border-light)',
                background: 'white',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'var(--text-secondary)',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                opacity: isProcessing ? 0.7 : 1
              }}
            >
              Skip
            </button>
            <button
              onClick={onConfirm}
              disabled={isProcessing}
              style={{
                padding: '8px 16px',
                borderRadius: '4px',
                border: 'none',
                background: 'var(--google-green)',
                fontFamily: "'Google Sans', sans-serif",
                fontSize: '14px',
                color: 'white',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                opacity: isProcessing ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span className="material-icons" style={{ fontSize: '18px' }}>check</span>
              Confirm
            </button>
          </>
        )}
      </div>
    </div>
  );
}
