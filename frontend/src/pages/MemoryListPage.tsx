/** Memory List Page */
import { useState, useEffect, useCallback } from 'react';
import { Plus, Filter, Tag, CheckCircle, Clock, ChevronLeft, ChevronRight, Trash2, Edit, ExternalLink } from 'lucide-react';
import { api } from '../api/client';
import type { MemoryUnit, MemoryUnitListResponse, PaginationParams, FilterParams } from '../types/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { ErrorBanner } from '../components/ErrorBanner';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { MemoryFormDialog } from '../components/MemoryFormDialog';
import { MemoryDetailDialog } from '../components/MemoryDetailDialog';
import { Database } from 'lucide-react';
import './MemoryListPage.css';
export function MemoryListPage() {
  const [memories, setMemories] = useState<MemoryUnit[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterParams>({});
  const [showFilters, setShowFilters] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<MemoryUnit | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingMemory, setEditingMemory] = useState<MemoryUnit | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<MemoryUnit | null>(null);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pagination: PaginationParams = { page, page_size: pageSize };
      const response: MemoryUnitListResponse = await api.listMemories(pagination, filters);
      setMemories(response.items);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memories');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const handleCreate = () => {
    setEditingMemory(null);
    setShowForm(true);
  };

  const handleEdit = (memory: MemoryUnit) => {
    setEditingMemory(memory);
    setShowForm(true);
  };

  const handleDelete = (memory: MemoryUnit) => {
    setDeleteConfirm(memory);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await api.deleteMemory(deleteConfirm.id);
      setDeleteConfirm(null);
      fetchMemories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete memory');
      setDeleteConfirm(null);
    }
  };

  const handleFormSubmit = async (data: { document_id: string; content: string; tags: string[] }) => {
    try {
      if (editingMemory) {
        await api.updateMemory(editingMemory.id, {
          content: data.content,
          tags: data.tags,
        });
      } else {
        await api.createMemory({
          document_id: data.document_id,
          content: data.content,
          tags: data.tags,
        });
      }
      setShowForm(false);
      setEditingMemory(null);
      fetchMemories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save memory');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading && memories.length === 0) {
    return (
      <div className="memory-list-page loading">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="memory-list-page">
      <ErrorBanner message={error} onDismiss={() => setError(null)} />

      <div className="page-header">
        <h2>Memory Units</h2>
        <div className="header-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="icon" size={18} />
            <span>Filters</span>
          </button>
          <button className="btn btn-primary" onClick={handleCreate}>
            <Plus className="icon" size={18} />
            <span>Add Memory</span>
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="filters-panel">
          <div className="filter-group">
            <label htmlFor="filter-document">Document ID</label>
            <input
              id="filter-document"
              type="text"
              placeholder="Filter by document..."
              value={filters.document_id || ''}
              onChange={(e) => setFilters({ ...filters, document_id: e.target.value || undefined })}
            />
          </div>
          <div className="filter-group">
            <label htmlFor="filter-tag">Tag</label>
            <input
              id="filter-tag"
              type="text"
              placeholder="Filter by tag..."
              value={filters.tag || ''}
              onChange={(e) => setFilters({ ...filters, tag: e.target.value || undefined })}
            />
          </div>
          <div className="filter-group">
            <label htmlFor="filter-search">Search Content</label>
            <input
              id="filter-search"
              type="text"
              placeholder="Search in content..."
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value || undefined })}
            />
          </div>
          <div className="filter-group">
            <label htmlFor="filter-consolidated">Consolidated</label>
            <select
              id="filter-consolidated"
              value={filters.is_consolidated === true ? 'true' : filters.is_consolidated === false ? 'false' : ''}
              onChange={(e) => setFilters({ ...filters, is_consolidated: e.target.value === 'true' ? true : e.target.value === 'false' ? false : undefined })}
            >
              <option value="">All</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>
      )}

      {memories.length === 0 && !loading && (
        <EmptyState
          icon={Database}
          title="No memories yet"
          description="Create your first memory unit to get started."
          actionLabel="Add Memory"
          onAction={handleCreate}
        />
      )}

      {memories.length > 0 && (
        <div className="memory-table-container">
          <table className="memory-table">
            <thead>
              <tr>
                <th>Content</th>
                <th>Document</th>
                <th>Tags</th>
                <th>Status</th>
                <th>Created</th>
                <th>Updated</th>
                <th className="actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {memories.map((memory) => (
                <tr key={memory.id}>
                  <td className="content-cell">
                    <div className="content-preview" title={memory.content}>
                      {memory.content.length > 100
                        ? memory.content.slice(0, 100) + '...'
                        : memory.content}
                    </div>
                  </td>
                  <td>
                    <span className="document-id">{memory.document_id}</span>
                  </td>
                  <td>
                    <div className="tags">
                      {memory.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="tag">
                          <Tag className="icon" size={12} />
                          {tag}
                        </span>
                      ))}
                      {memory.tags.length > 3 && (
                        <span className="tag more">+{memory.tags.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${memory.is_consolidated ? 'consolidated' : 'pending'}`}>
                      {memory.is_consolidated ? (
                        <>
                          <CheckCircle className="icon" size={14} />
                          Consolidated
                        </>
                      ) : (
                        <>
                          <Clock className="icon" size={14} />
                          Pending
                        </>
                      )}
                    </span>
                  </td>
                  <td>{formatDate(memory.created_at)}</td>
                  <td>{formatDate(memory.updated_at)}</td>
                  <td className="actions-col">
                    <div className="action-buttons">
                      <button
                        className="action-btn view"
                        onClick={() => setSelectedMemory(memory)}
                        title="View details"
                      >
                        <ExternalLink className="icon" size={16} />
                      </button>
                      <button
                        className="action-btn edit"
                        onClick={() => handleEdit(memory)}
                        title="Edit"
                      >
                        <Edit className="icon" size={16} />
                      </button>
                      <button
                        className="action-btn delete"
                        onClick={() => handleDelete(memory)}
                        title="Delete"
                      >
                        <Trash2 className="icon" size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <nav className="pagination" aria-label="Pagination">
          <button
            className="btn btn-ghost pagination-btn"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            aria-label="Previous page"
          >
            <ChevronLeft className="icon" size={18} />
          </button>
          <span className="pagination-info">
            Page {page} of {totalPages} ({total} total)
          </span>
          <button
            className="btn btn-ghost pagination-btn"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            aria-label="Next page"
          >
            <ChevronRight className="icon" size={18} />
          </button>
        </nav>
      )}

      {selectedMemory && (
        <MemoryDetailDialog
          memory={selectedMemory}
          onClose={() => setSelectedMemory(null)}
        />
      )}

      {showForm && (
        <MemoryFormDialog
          initialData={editingMemory
            ? { document_id: editingMemory.document_id, content: editingMemory.content, tags: editingMemory.tags }
            : undefined}
          onSubmit={handleFormSubmit}
          onClose={() => {
            setShowForm(false);
            setEditingMemory(null);
          }}
          isEditing={!!editingMemory}
        />
      )}

      {deleteConfirm && (
        <ConfirmDialog
          title="Delete Memory"
          message={`Are you sure you want to delete this memory unit? This action cannot be undone.`}
          onConfirm={confirmDelete}
          onCancel={() => setDeleteConfirm(null)}
          confirmLabel="Delete"
          variant="danger"
        />
      )}
    </div>
  );
}