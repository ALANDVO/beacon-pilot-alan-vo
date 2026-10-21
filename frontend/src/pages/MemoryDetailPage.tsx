/** Memory Detail Page */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Edit, Trash2, Copy, Tag, Calendar, Hash, FileText, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import { api } from '../api/client';
import type { MemoryUnit } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBanner } from '../components/ErrorBanner';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { MemoryFormDialog } from '../components/MemoryFormDialog';
import './MemoryDetailPage.css';

export function MemoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [memory, setMemory] = useState<MemoryUnit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  useEffect(() => {
    if (id) {
      fetchMemory();
    }
  }, [id]);

  const fetchMemory = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMemory(parseInt(id, 10));
      setMemory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memory');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (data: { document_id: string; content: string; tags: string[] }) => {
    if (!memory) return;
    try {
      await api.updateMemory(memory.id, {
        content: data.content,
        tags: data.tags,
      });
      setShowForm(false);
      fetchMemory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update memory');
    }
  };

  const handleDelete = async () => {
    if (!memory) return;
    try {
      await api.deleteMemory(memory.id);
      setDeleteConfirm(false);
      window.location.href = '/memories';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete memory');
      setDeleteConfirm(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="memory-detail-page loading">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!memory) {
    return (
      <div className="memory-detail-page">
        <ErrorBanner message={error || 'Memory not found'} onDismiss={() => setError(null)} />
        <div className="empty-detail">
          <ArrowLeft className="back-icon" size={24} />
          <Link to="/memories" className="back-link">
            Back to Memories
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="memory-detail-page">
      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      <div className="page-header">
        <Link to="/memories" className="back-link">
          <ArrowLeft className="icon" size={20} />
          Back
        </Link>
        <h2>Memory #{memory.id}</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => setShowForm(true)}>
            <Edit className="icon" size={18} />
            Edit
          </button>
          <button className="btn btn-danger" onClick={() => setDeleteConfirm(true)}>
            <Trash2 className="icon" size={18} />
            Delete
          </button>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-card content-card">
          <div className="card-header">
            <h3 className="card-title">
              <FileText className="icon" size={20} />
              Content
            </h3>
            <button className="copy-btn" onClick={() => copyToClipboard(memory.content)} title="Copy content">
              <Copy className="icon" size={18} />
            </button>
          </div>
          <pre className="content-text">{memory.content}</pre>
        </div>

        <div className="detail-card">
          <h3 className="card-title">
            <Hash className="icon" size={20} />
            Details
          </h3>
          <div className="detail-list">
            <div className="detail-row">
              <span className="detail-label">
                <FileText className="icon" size={16} />
                Document ID
              </span>
              <div className="detail-value">
                <code>{memory.document_id}</code>
                <button className="copy-btn" onClick={() => copyToClipboard(memory.document_id)} title="Copy">
                  <Copy className="icon" size={14} />
                </button>
              </div>
            </div>
            <div className="detail-row">
              <span className="detail-label">
                <Hash className="icon" size={16} />
                Content Hash
              </span>
              <div className="detail-value">
                <code>{memory.content_hash}</code>
                <button className="copy-btn" onClick={() => copyToClipboard(memory.content_hash)} title="Copy">
                  <Copy className="icon" size={14} />
                </button>
              </div>
            </div>
            <div className="detail-row">
              <span className="detail-label">
                <Calendar className="icon" size={16} />
                Created
              </span>
              <span className="detail-value">{formatDate(memory.created_at)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">
                <Calendar className="icon" size={16} />
                Updated
              </span>
              <span className="detail-value">{formatDate(memory.updated_at)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">
                {memory.is_consolidated ? (
                  <>
                    <CheckCircle className="icon" size={16} />
                    Status
                  </>
                ) : (
                  <>
                    <Clock className="icon" size={16} />
                    Status
                  </>
                )}
              </span>
              <span className="detail-value">
                <span className={`status-badge ${memory.is_consolidated ? 'consolidated' : 'pending'}`}>
                  {memory.is_consolidated ? 'Consolidated' : 'Pending'}
                </span>
              </span>
            </div>
            {memory.consolidated_at && (
              <div className="detail-row">
                <span className="detail-label">
                  <Calendar className="icon" size={16} />
                  Consolidated At
                </span>
                <span className="detail-value">{formatDate(memory.consolidated_at)}</span>
              </div>
            )}
            {memory.consolidation_batch_id && (
              <div className="detail-row">
                <span className="detail-label">
                  <ExternalLink className="icon" size={16} />
                  Batch ID
                </span>
                <div className="detail-value">
                  <code>{memory.consolidation_batch_id}</code>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {memory.tags.length > 0 && (
        <div className="detail-card tags-card">
          <h3 className="card-title">
            <Tag className="icon" size={20} />
            Tags
          </h3>
          <div className="tags">
            {memory.tags.map((tag) => (
              <span key={tag} className="tag">
                <Tag className="icon" size={14} />
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {Object.keys(memory.metadata).length > 0 && (
        <div className="detail-card">
          <h3 className="card-title">Metadata</h3>
          <pre className="metadata-display">{JSON.stringify(memory.metadata, null, 2)}</pre>
        </div>
      )}

      {memory.observation_scopes.length > 0 && (
        <div className="detail-card">
          <h3 className="card-title">Observation Scopes</h3>
          <div className="tags">
            {memory.observation_scopes.map((scope) => (
              <span key={scope} className="tag scope-tag">
                <Tag className="icon" size={14} />
                {scope}
              </span>
            ))}
          </div>
        </div>
      )}

      {showForm && (
        <MemoryFormDialog
          initialData={{ document_id: memory.document_id, content: memory.content, tags: memory.tags }}
          onSubmit={handleUpdate}
          onClose={() => setShowForm(false)}
          isEditing={true}
        />
      )}

      {deleteConfirm && (
        <ConfirmDialog
          title="Delete Memory"
          message={`Are you sure you want to delete memory #${memory.id}? This action cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setDeleteConfirm(false)}
          confirmLabel="Delete"
          variant="danger"
        />
      )}
    </div>
  );
}