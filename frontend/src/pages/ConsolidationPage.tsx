/** Consolidation Page */
import { useState, useEffect, useCallback } from 'react';
import { GitMerge, Play, Loader2, CheckCircle, AlertCircle, FileText, Clock, X } from 'lucide-react';
import { api } from '../api/client';
import type { ConsolidationBatch, ConsolidationReport } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { ErrorBanner } from '../components/ErrorBanner';
import './ConsolidationPage.css';

export function ConsolidationPage() {
  const [batches, setBatches] = useState<ConsolidationBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<ConsolidationBatch | null>(null);
  const [report, setReport] = useState<ConsolidationReport | null>(null);
  const [runningBatchId, setRunningBatchId] = useState<string | null>(null);
  const [newDocumentId, setNewDocumentId] = useState('');

  const fetchBatches = useCallback(async () => {
    try {
      // We'll need to implement a list endpoint; for now fetch from memories
      const memoriesResponse = await api.listMemories({ page_size: 100 });
      const docIds = [...new Set(memoriesResponse.items.map(m => m.document_id))];
      
      // Create mock batches for demo - in real app this would come from a batches list endpoint
      // For now we'll just show documents that can be consolidated
      const mockBatches: ConsolidationBatch[] = docIds.map((docId) => ({
        id: `batch-${docId}`,
        document_id: docId,
        status: 'pending' as const,
        units_processed: 0,
        units_created: 0,
        units_merged: 0,
        units_deleted: 0,
        error_message: null,
        metadata: {},
        started_at: new Date().toISOString(),
        completed_at: null,
      }));
      setBatches(mockBatches);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load batches');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  const handleCreateBatch = async () => {
    if (!newDocumentId.trim()) return;
    setError(null);
    try {
      const batch = await api.createConsolidationBatch(newDocumentId.trim());
      setBatches(prev => [batch, ...prev]);
      setNewDocumentId('');
      setSelectedBatch(batch);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create batch');
    }
  };

  const handleRunBatch = async (batch: ConsolidationBatch) => {
    setRunningBatchId(batch.id);
    setError(null);
    try {
      const result = await api.runConsolidation(batch.id);
      setReport(result);
      setSelectedBatch({ ...batch, status: 'completed' });
      setBatches(prev => prev.map(b => b.id === batch.id ? { ...b, status: 'completed' } : b));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run consolidation');
      setBatches(prev => prev.map(b => b.id === batch.id ? { ...b, status: 'failed' } : b));
    } finally {
      setRunningBatchId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status: ConsolidationBatch['status']) => {
    switch (status) {
      case 'pending': return <Clock className="icon" size={16} />;
      case 'running': return <Loader2 className="icon spin" size={16} />;
      case 'completed': return <CheckCircle className="icon" size={16} />;
      case 'failed': return <AlertCircle className="icon" size={16} />;
    }
  };

  const getStatusColor = (status: ConsolidationBatch['status']) => {
    switch (status) {
      case 'pending': return 'var(--color-text-muted)';
      case 'running': return 'var(--color-primary)';
      case 'completed': return 'var(--color-success)';
      case 'failed': return 'var(--color-error)';
    }
  };

  if (loading) {
    return (
      <div className="consolidation-page loading">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="consolidation-page">
      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      <div className="page-header">
        <h2>
          <GitMerge className="icon" size={28} />
          Consolidation
        </h2>
        <p className="page-description">
          Deduplicate and merge similar memory units within a document.
        </p>
      </div>

      <div className="create-batch-section">
        <h3>Create New Consolidation Batch</h3>
        <div className="create-batch-form">
          <div className="input-group">
            <label htmlFor="document-id">Document ID</label>
            <input
              id="document-id"
              type="text"
              value={newDocumentId}
              onChange={(e) => setNewDocumentId(e.target.value)}
              placeholder="Enter document ID to consolidate"
            />
          </div>
          <button className="btn btn-primary" onClick={handleCreateBatch} disabled={!newDocumentId.trim()}>
            <GitMerge className="icon" size={18} />
            Create Batch
          </button>
        </div>
      </div>

      <div className="batches-section">
        <h3>Consolidation Batches</h3>
        
        {batches.length === 0 && (
          <EmptyState
            icon={FileText}
            title="No batches yet"
            description="Create a consolidation batch for a document to get started."
          />
        )}

        {batches.length > 0 && (
          <div className="batches-table-container">
            <table className="batches-table">
              <thead>
                <tr>
                  <th>Document ID</th>
                  <th>Status</th>
                  <th>Units Before</th>
                  <th>Units After</th>
                  <th>Merged</th>
                  <th>Deleted</th>
                  <th>Duration</th>
                  <th>Started</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch) => (
                  <tr key={batch.id}>
                    <td>
                      <code className="document-id">{batch.document_id}</code>
                    </td>
                    <td>
                      <span className="status-badge" style={{ color: getStatusColor(batch.status) }}>
                        {getStatusIcon(batch.status)}
                        <span className="status-text">{batch.status}</span>
                      </span>
                    </td>
                    <td>{report?.units_before ?? batch.units_processed ?? '-'}</td>
                    <td>{report?.units_after ?? '-'}</td>
                    <td>{report?.merged_pairs.length ?? batch.units_merged ?? '-'}</td>
                    <td>{report?.deleted_ids.length ?? batch.units_deleted ?? '-'}</td>
                    <td>{report?.duration_ms ? `${report.duration_ms}ms` : '-'}</td>
                    <td>{formatDate(batch.started_at)}</td>
                    <td>
                      <div className="action-buttons">
                        {batch.status === 'pending' && (
                          <button
                            className="action-btn run"
                            onClick={() => handleRunBatch(batch)}
                            disabled={runningBatchId !== null}
                            title="Run consolidation"
                          >
                            {runningBatchId === batch.id ? (
                              <Loader2 className="icon spin" size={16} />
                            ) : (
                              <Play className="icon" size={16} />
                            )}
                          </button>
                        )}
                        {batch.status === 'completed' && report && (
                          <button
                            className="action-btn view"
                            onClick={() => setSelectedBatch(batch)}
                            title="View report"
                          >
                            <CheckCircle className="icon" size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedBatch && report && (
        <ConsolidationReportDialog
          report={report}
          onClose={() => setSelectedBatch(null)}
        />
      )}
    </div>
  );
}

function ConsolidationReportDialog({ report, onClose }: { report: ConsolidationReport; onClose: () => void }) {
  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog dialog-lg" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h3 className="dialog-title">Consolidation Report</h3>
          <button className="dialog-close" onClick={onClose} aria-label="Close">
            <X className="icon" size={20} />
          </button>
        </div>
        <div className="dialog-body">
          <div className="report-summary">
            <div className="summary-item">
              <span className="summary-label">Document</span>
              <span className="summary-value"><code>{report.document_id}</code></span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Batch ID</span>
              <span className="summary-value"><code>{report.batch_id.slice(0, 12)}...</code></span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Units Before</span>
              <span className="summary-value">{report.units_before}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Units After</span>
              <span className="summary-value">{report.units_after}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Duplicates Found</span>
              <span className="summary-value">{report.duplicates_found}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Merged Pairs</span>
              <span className="summary-value">{report.merged_pairs.length}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Deleted</span>
              <span className="summary-value">{report.deleted_ids.length}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Duration</span>
              <span className="summary-value">{report.duration_ms}ms</span>
            </div>
          </div>

          {report.merged_pairs.length > 0 && (
            <div className="report-section">
              <h4>Merged Pairs</h4>
              <div className="merged-pairs">
                {report.merged_pairs.map(([primary, duplicate], index) => (
                  <div key={index} className="merged-pair">
                    <span>#{primary} ← #{duplicate}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.deleted_ids.length > 0 && (
            <div className="report-section">
              <h4>Deleted Units</h4>
              <div className="deleted-ids">
                {report.deleted_ids.map((id) => (
                  <span key={id} className="deleted-id">#{id}</span>
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