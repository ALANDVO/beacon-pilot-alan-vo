/** Memory Form Dialog Component */
import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import './MemoryFormDialog.css';

interface MemoryFormData {
  document_id: string;
  content: string;
  tags: string[];
}

interface MemoryFormDialogProps {
  initialData?: MemoryFormData;
  onSubmit: (data: MemoryFormData) => void;
  onClose: () => void;
  isEditing?: boolean;
}

export function MemoryFormDialog({ initialData, onSubmit, onClose, isEditing = false }: MemoryFormDialogProps) {
  const [documentId, setDocumentId] = useState(initialData?.document_id || '');
  const [content, setContent] = useState(initialData?.content || '');
  const [tagsInput, setTagsInput] = useState(initialData?.tags.join(', ') || '');
  const [errors, setErrors] = useState<Partial<Record<keyof MemoryFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setDocumentId(initialData.document_id);
      setContent(initialData.content);
      setTagsInput(initialData.tags.join(', '));
    }
  }, [initialData]);

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof MemoryFormData, string>> = {};
    if (!documentId.trim()) newErrors.document_id = 'Document ID is required';
    if (!content.trim()) newErrors.content = 'Content is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      await onSubmit({
        document_id: documentId.trim(),
        content: content.trim(),
        tags: tagsInput.split(',').map(t => t.trim()).filter(Boolean),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) onClose();
  };

  return (
    <div className="dialog-overlay" onClick={handleClose}>
      <div className="dialog dialog-lg" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h3 className="dialog-title">{isEditing ? 'Edit Memory' : 'Create Memory'}</h3>
          <button className="dialog-close" onClick={handleClose} aria-label="Close">
            <X className="icon" size={20} />
          </button>
        </div>
        <form id="memory-form" onSubmit={handleSubmit} className="dialog-body">
          <div className="form-group">
            <label htmlFor="document_id" className="form-label">
              Document ID <span className="required">*</span>
            </label>
            <input
              id="document_id"
              type="text"
              className={`form-input ${errors.document_id ? 'error' : ''}`}
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
              placeholder="e.g., session-abc123"
              disabled={isEditing}
            />
            {errors.document_id && <span className="form-error">{errors.document_id}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="content" className="form-label">
              Content <span className="required">*</span>
            </label>
            <textarea
              id="content"
              className={`form-textarea ${errors.content ? 'error' : ''}`}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter the memory content..."
              rows={6}
            />
            {errors.content && <span className="form-error">{errors.content}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="tags" className="form-label">
              Tags
            </label>
            <input
              id="tags"
              type="text"
              className="form-input"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="tag1, tag2, tag3 (comma-separated)"
            />
            <span className="form-hint">Separate tags with commas</span>
          </div>
        </form>
        <div className="dialog-footer">
          <button type="button" className="btn btn-secondary" onClick={handleClose} disabled={submitting}>
            Cancel
          </button>
          <button type="submit" form="memory-form" className="btn btn-primary" disabled={submitting}>
            {submitting ? (
              <>
                <span className="spinner-sm" />
                {isEditing ? 'Saving...' : 'Creating...'}
              </>
            ) : (
              isEditing ? 'Save Changes' : 'Create Memory'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}