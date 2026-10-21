/** Memory Detail Dialog Component */
import { X, Copy, Tag, Calendar, Hash, FileText, CheckCircle, Clock } from 'lucide-react';
import './MemoryDetailDialog.css';
import type { MemoryUnit } from '../types/api';

interface MemoryDetailDialogProps {
  memory: MemoryUnit;
  onClose: () => void;
}

export function MemoryDetailDialog({ memory, onClose }: MemoryDetailDialogProps) {
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

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog dialog-xl" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h3 className="dialog-title">Memory Details</h3>
          <button className="dialog-close" onClick={onClose} aria-label="Close">
            <X className="icon" size={20} />
          </button>
        </div>
        <div className="dialog-body">
          <div className="detail-section">
            <h4 className="section-title">Content</h4>
            <div className="content-display">
              <pre className="content-text">{memory.content}</pre>
              <button
                className="copy-btn"
                onClick={() => copyToClipboard(memory.content)}
                title="Copy content"
              >
                <Copy className="icon" size={16} />
              </button>
            </div>
          </div>

          <div className="detail-grid">
            <div className="detail-item">
              <div className="detail-label">
                <FileText className="icon" size={16} />
                Document ID
              </div>
              <div className="detail-value">
                <code>{memory.document_id}</code>
                <button className="copy-btn" onClick={() => copyToClipboard(memory.document_id)} title="Copy">
                  <Copy className="icon" size={14} />
                </button>
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-label">
                <Hash className="icon" size={16} />
                Content Hash
              </div>
              <div className="detail-value">
                <code>{memory.content_hash.slice(0, 16)}...</code>
                <button className="copy-btn" onClick={() => copyToClipboard(memory.content_hash)} title="Copy">
                  <Copy className="icon" size={14} />
                </button>
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-label">
                <Calendar className="icon" size={16} />
                Created
              </div>
              <div className="detail-value">{formatDate(memory.created_at)}</div>
            </div>

            <div className="detail-item">
              <div className="detail-label">
                <Calendar className="icon" size={16} />
                Updated
              </div>
              <div className="detail-value">{formatDate(memory.updated_at)}</div>
            </div>

            <div className="detail-item">
              <div className="detail-label">
                {memory.is_consolidated ? (
                  <>
                    <CheckCircle className="icon" size={16} />
                    Consolidated
                  </>
                ) : (
                  <>
                    <Clock className="icon" size={16} />
                    Status
                  </>
                )}
              </div>
              <div className="detail-value">
                <span className={`status-badge ${memory.is_consolidated ? 'consolidated' : 'pending'}`}>
                  {memory.is_consolidated ? 'Consolidated' : 'Pending'}
                </span>
              </div>
            </div>

            {memory.consolidated_at && (
              <div className="detail-item">
                <div className="detail-label">
                  <Calendar className="icon" size={16} />
                  Consolidated At
                </div>
                <div className="detail-value">{formatDate(memory.consolidated_at)}</div>
              </div>
            )}

            {memory.consolidation_batch_id && (
              <div className="detail-item">
                <div className="detail-label">
                  <Hash className="icon" size={16} />
                  Batch ID
                </div>
                <div className="detail-value">
                  <code>{memory.consolidation_batch_id.slice(0, 12)}...</code>
                </div>
              </div>
            )}
          </div>

          {memory.tags.length > 0 && (
            <div className="detail-section">
              <h4 className="section-title">Tags</h4>
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
            <div className="detail-section">
              <h4 className="section-title">Metadata</h4>
              <pre className="metadata-display">{JSON.stringify(memory.metadata, null, 2)}</pre>
            </div>
          )}

          {memory.observation_scopes.length > 0 && (
            <div className="detail-section">
              <h4 className="section-title">Observation Scopes</h4>
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
        </div>
        <div className="dialog-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}