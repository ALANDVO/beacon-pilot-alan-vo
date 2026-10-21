/// <reference types="vitest/globals" />
/** Frontend tests for MemoryListPage */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MemoryListPage } from '../pages/MemoryListPage';
import { api } from '../api/client';

// Mock the API client
vi.mock('../api/client', () => ({
  api: {
    listMemories: vi.fn(),
    createMemory: vi.fn(),
    updateMemory: vi.fn(),
    deleteMemory: vi.fn(),
  },
}));

const mockMemories = [
  {
    id: 1,
    document_id: 'doc-1',
    content: 'Test memory content 1',
    content_hash: 'abc123',
    tags: ['tag1', 'tag2'],
    metadata: { source: 'test' },
    observation_scopes: ['scope1'],
    is_consolidated: false,
    consolidated_at: null,
    consolidation_batch_id: null,
    created_at: '2024-01-01T12:00:00Z',
    updated_at: '2024-01-01T12:00:00Z',
  },
  {
    id: 2,
    document_id: 'doc-2',
    content: 'Test memory content 2',
    content_hash: 'def456',
    tags: ['tag2'],
    metadata: {},
    observation_scopes: [],
    is_consolidated: true,
    consolidated_at: '2024-01-02T12:00:00Z',
    consolidation_batch_id: 'batch-1',
    created_at: '2024-01-01T13:00:00Z',
    updated_at: '2024-01-02T12:00:00Z',
  },
];

const mockListResponse = {
  items: mockMemories,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

describe('MemoryListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.listMemories as vi.Mock).mockResolvedValue(mockListResponse);
  });

  const renderPage = () => {
    return render(
      <BrowserRouter>
        <MemoryListPage />
      </BrowserRouter>
    );
  };

  it('renders loading spinner initially', () => {
    (api.listMemories as vi.Mock).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(mockListResponse), 100)));
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays memory list after loading', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Test memory content 1')).toBeInTheDocument();
      expect(screen.getByText('Test memory content 2')).toBeInTheDocument();
    });
  });

  it('shows correct memory details in table', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('doc-1')).toBeInTheDocument();
      expect(screen.getByText('doc-2')).toBeInTheDocument();
      expect(screen.getByText('tag1')).toBeInTheDocument();
      const tag2Elements = screen.getAllByText('tag2');
      expect(tag2Elements.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('shows consolidated status badge', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Consolidated')).toBeInTheDocument();
    });
  });

  it('opens create form when Add Memory button clicked', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Add Memory')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: 'Add Memory' }));
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Create Memory' })).toBeInTheDocument();
      expect(screen.getByLabelText('Document ID *')).toBeInTheDocument();
      expect(screen.getByLabelText('Content *')).toBeInTheDocument();
    });
  });

  it('calls createMemory on form submit', async () => {
    (api.createMemory as vi.Mock).mockResolvedValue({ ...mockMemories[0], id: 3 });
    renderPage();
    
    await waitFor(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Add Memory' }));
    });
    
    fireEvent.change(screen.getByLabelText('Document ID *'), { target: { value: 'new-doc' } });
    fireEvent.change(screen.getByLabelText('Content *'), { target: { value: 'New memory content' } });
    fireEvent.change(screen.getByLabelText('Tags'), { target: { value: 'new, tags' } });
    
    fireEvent.click(screen.getByRole('button', { name: 'Create Memory' }));
    
    await waitFor(() => {
      expect(api.createMemory).toHaveBeenCalledWith({
        document_id: 'new-doc',
        content: 'New memory content',
        tags: ['new', 'tags'],
      });
    });
  });

  it('opens edit form when edit button clicked', async () => {
    (api.updateMemory as vi.Mock).mockResolvedValue(mockMemories[0]);
    renderPage();
    
    await waitFor(() => {
      const editButtons = screen.getAllByRole('button', { name: 'Edit' });
      fireEvent.click(editButtons[0]);
    });
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Edit Memory' })).toBeInTheDocument();
      expect(screen.getByLabelText('Document ID *')).toHaveValue('doc-1');
      expect(screen.getByLabelText('Content *')).toHaveValue('Test memory content 1');
    });
  });

  it('shows delete confirmation dialog', async () => {
    (api.deleteMemory as vi.Mock).mockResolvedValue(undefined);
    renderPage();
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
      fireEvent.click(deleteButtons[0]);
    });
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Delete Memory' })).toBeInTheDocument();
      expect(screen.getByText(/Are you sure you want to delete this memory unit/)).toBeInTheDocument();
    });
  });

  it('calls deleteMemory on confirm delete', async () => {
    (api.deleteMemory as vi.Mock).mockResolvedValue(undefined);
    renderPage();
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
      fireEvent.click(deleteButtons[0]);
    });
    
    // Click the confirm button in the dialog (the danger button)
    const dialogButtons = screen.getAllByRole('button');
    const confirmBtn = dialogButtons.find(btn => btn.classList.contains('btn-danger'));
    fireEvent.click(confirmBtn!);
    
    await waitFor(() => {
      expect(api.deleteMemory).toHaveBeenCalledWith(1);
    });
  });

  it('shows error banner on API error', async () => {
    (api.listMemories as vi.Mock).mockRejectedValue(new Error('Network error'));
    renderPage();
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('displays pagination info', async () => {
    // Mock a response with multiple pages
    (api.listMemories as vi.Mock).mockResolvedValue({
      items: mockMemories,
      total: 25,
      page: 1,
      page_size: 20,
      total_pages: 2,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2 (25 total)')).toBeInTheDocument();
    });
  });
});