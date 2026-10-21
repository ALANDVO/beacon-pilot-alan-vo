/** Typed API Client */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  MemoryUnit,
  MemoryUnitCreate,
  MemoryUnitUpdate,
  MemoryUnitListResponse,
  ConsolidationBatch,
  ConsolidationReport,
  HealthResponse,
  ErrorResponse,
  PaginationParams,
  FilterParams,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = sessionStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response?.status === 401) {
          // Clear auth and redirect to login
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Health
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Memories
  async listMemories(
    pagination: PaginationParams = {},
    filters: FilterParams = {}
  ): Promise<MemoryUnitListResponse> {
    const params = { ...pagination, ...filters };
    const response = await this.client.get<MemoryUnitListResponse>('/memories', { params });
    return response.data;
  }

  async getMemory(id: number): Promise<MemoryUnit> {
    const response = await this.client.get<MemoryUnit>(`/memories/${id}`);
    return response.data;
  }

  async createMemory(data: MemoryUnitCreate): Promise<MemoryUnit> {
    const response = await this.client.post<MemoryUnit>('/memories', data);
    return response.data;
  }

  async updateMemory(id: number, data: MemoryUnitUpdate): Promise<MemoryUnit> {
    const response = await this.client.patch<MemoryUnit>(`/memories/${id}`, data);
    return response.data;
  }

  async deleteMemory(id: number): Promise<void> {
    await this.client.delete(`/memories/${id}`);
  }

  // Consolidation
  async createConsolidationBatch(documentId: string): Promise<ConsolidationBatch> {
    const response = await this.client.post<ConsolidationBatch>('/consolidate', {
      document_id: documentId,
    });
    return response.data;
  }

  async getConsolidationBatch(batchId: string): Promise<ConsolidationBatch> {
    const response = await this.client.get<ConsolidationBatch>(`/consolidate/${batchId}`);
    return response.data;
  }

  async runConsolidation(batchId: string): Promise<ConsolidationReport> {
    const response = await this.client.post<ConsolidationReport>(`/consolidate/${batchId}/run`);
    return response.data;
  }
}

export const api = new ApiClient();