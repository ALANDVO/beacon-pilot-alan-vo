/** API Type Definitions */

export interface MemoryUnit {
  id: number;
  document_id: string;
  content: string;
  content_hash: string;
  tags: string[];
  metadata: Record<string, unknown>;
  observation_scopes: string[];
  is_consolidated: boolean;
  consolidated_at: string | null;
  consolidation_batch_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemoryUnitCreate {
  document_id: string;
  content: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  observation_scopes?: string[];
}

export interface MemoryUnitUpdate {
  content?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  observation_scopes?: string[];
  is_consolidated?: boolean;
  consolidated_at?: string | null;
  consolidation_batch_id?: string | null;
}

export interface MemoryUnitListResponse {
  items: MemoryUnit[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface MemoryObservation {
  id: number;
  source_memory_id: number;
  target_memory_id: number;
  observation_type: string;
  confidence: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ConsolidationBatch {
  id: string;
  document_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  units_processed: number;
  units_created: number;
  units_merged: number;
  units_deleted: number;
  error_message: string | null;
  metadata: Record<string, unknown>;
  started_at: string;
  completed_at: string | null;
}

export interface ConsolidationReport {
  batch_id: string;
  document_id: string;
  units_before: number;
  units_after: number;
  duplicates_found: number;
  merged_pairs: [number, number][];
  deleted_ids: number[];
  new_units: MemoryUnit[];
  duration_ms: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface FilterParams {
  document_id?: string;
  tag?: string;
  is_consolidated?: boolean;
  search?: string;
}