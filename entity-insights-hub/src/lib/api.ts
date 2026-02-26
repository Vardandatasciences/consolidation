/**
 * API Service for communicating with Flask backend
 */
// 
// const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://finance.vardaands.com/api';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Log API base URL for debugging
console.log('[API Config] Base URL:', API_BASE_URL);


interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  warnings?: string[];
}

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: number;
    username: string;
    email: string;
    role: string;
    ent_id?: number | null;
  };
}

interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

/**
 * Generic API call handler
 */
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const token = localStorage.getItem('token');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const url = `${API_BASE_URL}${endpoint}`;
    console.log(`[API] ${options.method || 'GET'} ${url}`);
    
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error(`Server returned non-JSON response: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!response.ok) {
      console.error(`[API Error] ${response.status}:`, data);
      throw new Error(data.message || `Server error: ${response.status} ${response.statusText}`);
    }
    
    console.log(`[API Success] ${options.method || 'GET'} ${endpoint}:`, data);
    return data;
  } catch (error: any) {
    console.error('[API Error]', error);
    
    // Handle network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to server. Please check if the backend is running.');
    }
    
    // Re-throw with original message if it's already an Error
    if (error instanceof Error) {
      throw error;
    }
    
    throw new Error(error.message || 'An unexpected error occurred');
  }
}

/**
 * Authentication API calls
 */
export const authApi = {
  /**
   * Login user
   */
  login: async (credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> => {
    const response = await apiCall<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    // Store token in localStorage
    if (response.success && response.data?.token) {
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    
    return response;
  },
  
  /**
   * Register new user
   */
  register: async (userData: RegisterRequest): Promise<ApiResponse> => {
    return apiCall('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },
  
  /**
   * Verify token
   */
  verify: async (): Promise<ApiResponse> => {
    return apiCall('/auth/verify', {
      method: 'GET',
    });
  },
  
  /**
   * Logout user
   */
  logout: async (): Promise<ApiResponse> => {
    try {
      // Call backend logout endpoint (optional - mainly for server-side logging)
      try {
        await apiCall('/auth/logout', {
          method: 'POST',
        });
      } catch (error) {
        // Even if backend call fails, continue with client-side logout
        console.warn('Backend logout call failed, continuing with client-side logout:', error);
      }
      
      // Clear local storage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      return {
        success: true,
        message: 'Logout successful'
      };
    } catch (error: any) {
      // Clear local storage even if there's an error
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      return {
        success: true,
        message: 'Logout successful'
      };
    }
  },
  
  /**
   * Get current user from localStorage
   */
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  
  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('token');
  },
};

/**
 * Test API connection
 */
export const testApi = {
  test: async (): Promise<ApiResponse> => {
    return apiCall('/test', {
      method: 'GET',
    });
  },
  
  health: async (): Promise<ApiResponse> => {
    return apiCall('/health', {
      method: 'GET',
    });
  },
};

/**
 * Structured Data API calls
 */
export const structuredDataApi = {
  /**
   * Get structured data
   */
  getData: async (entityId?: number, financialYear?: number): Promise<ApiResponse<{ records: any[], total_assets: number, count: number }>> => {
    const params = new URLSearchParams();
    if (entityId) params.append('entity_id', entityId.toString());
    if (financialYear) params.append('financial_year', financialYear.toString());
    
    const queryString = params.toString();
    const endpoint = queryString ? `/structure/data?${queryString}` : '/structure/data';
    
    return apiCall<{ records: any[], total_assets: number, count: number }>(endpoint, {
      method: 'GET',
    });
  },
  
  /**
   * Get summary statistics
   */
  getSummary: async (entityId?: number, financialYear?: number): Promise<ApiResponse<{ summary: any[] }>> => {
    const params = new URLSearchParams();
    if (entityId) params.append('entity_id', entityId.toString());
    if (financialYear) params.append('financial_year', financialYear.toString());
    
    const queryString = params.toString();
    const endpoint = queryString ? `/structure/summary?${queryString}` : '/structure/summary';
    
    return apiCall<{ summary: any[] }>(endpoint, {
      method: 'GET',
    });
  },
  
  /**
   * Update final_structured table by matching particular field
   */
  updateByParticular: async (particular: string): Promise<ApiResponse<{ updated_count: number, code_data: any }>> => {
    return apiCall<{ updated_count: number, code_data: any }>('/structure/update-by-particular', {
      method: 'PUT',
      body: JSON.stringify({ particular }),
    });
  },
  
  /**
   * Recalculate Avg_Fx_Rt for all rows based on Brd_Cls and current forex rates
   */
  recalculateAvgFxRate: async (currency?: string): Promise<ApiResponse<{ updated_count: number, rates: any }>> => {
    return apiCall<{ updated_count: number, rates: any }>('/structure/recalculate-avg-fx-rate', {
      method: 'POST',
      body: JSON.stringify({ currency: currency || 'USDIN' }),
    });
  },
  
  /**
   * Export structured data to Excel file
   */
  exportToExcel: async (entityId?: number, financialYear?: number, entityCode?: string): Promise<Blob> => {
    const params = new URLSearchParams();
    if (entityId) params.append('entity_id', entityId.toString());
    if (financialYear) params.append('financial_year', financialYear.toString());
    if (entityCode) params.append('entity_code', entityCode);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/structure/export-excel?${queryString}` : '/structure/export-excel';
    const url = `${API_BASE_URL}${endpoint}`;
    
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Export failed' }));
      throw new Error(errorData.message || `Export failed: ${response.status} ${response.statusText}`);
    }
    
    return response.blob();
  },
  
  /**
   * Delete all records from rawdata and final_structured tables
   */
  deleteAll: async (): Promise<ApiResponse<{ deleted_count: number, rawdata_count: number, final_structured_count: number }>> => {
    return apiCall<{ deleted_count: number, rawdata_count: number, final_structured_count: number }>('/structure/delete-all', {
      method: 'DELETE',
    });
  },
  
  /**
   * Get consolidation data for an entity and its descendants
   */
  getConsolidation: async (entityId: number, financialYear?: string): Promise<ApiResponse<{
    balance_sheet: Record<string, Record<string, Record<number, number>>>;
    profit_loss: Record<string, Record<string, Record<number, number>>>;
    entities: Array<{ ent_id: number; ent_name: string; ent_code: string }>;
  }>> => {
    const params = new URLSearchParams();
    params.append('entity_id', entityId.toString());
    if (financialYear) params.append('financial_year', financialYear);
    
    return apiCall<{
      balance_sheet: Record<string, Record<string, Record<number, number>>>;
      profit_loss: Record<string, Record<string, Record<number, number>>>;
      entities: Array<{ ent_id: number; ent_name: string; ent_code: string }>;
    }>(`/structure/consolidation?${params.toString()}`, {
      method: 'GET',
    });
  },
};

/**
 * Upload API calls
 */
export const uploadApi = {
  /**
   * Get all entities
   */
  getEntities: async (): Promise<ApiResponse<{ entities: any[] }>> => {
    return apiCall<{ entities: any[] }>('/upload/entities', {
      method: 'GET',
    });
  },
  
  /**
   * Get all months
   */
  getMonths: async (): Promise<ApiResponse<{ months: any[] }>> => {
    return apiCall<{ months: any[] }>('/upload/months', {
      method: 'GET',
    });
  },
  
  /**
   * Get financial years
   */
  getFinancialYears: async (): Promise<ApiResponse<{ years: number[] }>> => {
    return apiCall<{ years: number[] }>('/upload/financial-years', {
      method: 'GET',
    });
  },
  
  /**
   * Upload file
   */
  uploadFile: async (file: File, entId: string, monthName: string, financialYear: string, operationId?: string, newCompany?: number): Promise<ApiResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ent_id', entId);
    formData.append('month_name', monthName);
    formData.append('financial_year', financialYear);
    if (operationId) {
      formData.append('operation_id', operationId);
    }
    if (newCompany !== undefined && newCompany !== null) {
      formData.append('newCompany', newCompany.toString());
    }
    
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      console.log('[Upload] Token found, setting Authorization header');
    } else {
      console.error('[Upload] No token found in localStorage!');
      throw new Error('Authentication token not found. Please login again.');
    }
    
    const url = `${API_BASE_URL}/upload/upload`;
    console.log('[Upload] Sending request to:', url);
    console.log('[Upload] File:', file.name, file.size, 'bytes');
    console.log('[Upload] Form data:', { entId, monthName, financialYear });
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });
    
    console.log('[Upload] Response status:', response.status);
    
    const data = await response.json();
    console.log('[Upload] Response data:', data);
    
    if (!response.ok) {
      const errorMsg = data.message || data.error || 'File upload failed';
      console.error('[Upload] Error:', errorMsg, data);
      throw new Error(errorMsg);
    }
    
    return data;
  },

  /**
   * Poll upload progress by operation id
   */
  getUploadProgress: async (operationId: string): Promise<ApiResponse<{ status: string; progress: number; message?: string; processed_rows?: number; total_rows?: number; meta?: any }>> => {
    return apiCall(`/upload/progress/${operationId}`, {
      method: 'GET',
    });
  },
};

/**
 * Entity API calls
 */
export const entityApi = {
  /**
   * List entities
   */
  list: async (): Promise<ApiResponse<{ entities: any[] }>> => {
    return apiCall<{ entities: any[] }>('/entities', {
      method: 'GET',
    });
  },

  /**
   * Create entity
   */
  create: async (payload: {
    ent_name: string;
    ent_code: string;
    lcl_curr: string;
    city?: string;
    country?: string;
    parent_entity_id?: number | null;
  }): Promise<ApiResponse<any>> => {
    return apiCall<any>('/entities', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update entity
   */
  update: async (entId: number, payload: {
    ent_name: string;
    ent_code: string;
    lcl_curr: string;
    city?: string;
    country?: string;
    parent_entity_id?: number | null;
  }): Promise<ApiResponse<any>> => {
    return apiCall<any>(`/entities/${entId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Delete entity
   */
  delete: async (entId: number): Promise<ApiResponse<any>> => {
    return apiCall<any>(`/entities/${entId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get children of an entity
   */
  getChildren: async (entId: number): Promise<ApiResponse<{ entity_id: number; entity_name: string; children: any[] }>> => {
    return apiCall<{ entity_id: number; entity_name: string; children: any[] }>(`/entities/${entId}/children`, {
      method: 'GET',
    });
  },

  /**
   * Get parent of an entity
   */
  getParent: async (entId: number): Promise<ApiResponse<{ entity_id: number; parent: any | null }>> => {
    return apiCall<{ entity_id: number; parent: any | null }>(`/entities/${entId}/parent`, {
      method: 'GET',
    });
  },

  /**
   * Get all descendants of an entity
   */
  getDescendants: async (entId: number): Promise<ApiResponse<{ entity_id: number; entity_name: string; descendants: any[] }>> => {
    return apiCall<{ entity_id: number; entity_name: string; descendants: any[] }>(`/entities/${entId}/descendants`, {
      method: 'GET',
    });
  },

  /**
   * Get full hierarchy (entity, parent, children, grandchildren)
   */
  getHierarchy: async (entId: number): Promise<ApiResponse<{
    entity: any;
    parent: any | null;
    children: any[];
    grandchildren: any[];
  }>> => {
    return apiCall<{
      entity: any;
      parent: any | null;
      children: any[];
      grandchildren: any[];
    }>(`/entities/${entId}/hierarchy`, {
      method: 'GET',
    });
  },

  /**
   * Get root entities (entities with no parent)
   */
  getRootEntities: async (): Promise<ApiResponse<{ entities: any[] }>> => {
    return apiCall<{ entities: any[] }>('/entities/roots', {
      method: 'GET',
    });
  },
};

/**
 * Code Master API calls
 */
export const codeMasterApi = {
  list: async (): Promise<ApiResponse<{ codes: any[] }>> => {
    return apiCall<{ codes: any[] }>('/code-master', { method: 'GET' });
  },
  getByParticular: async (particular: string): Promise<ApiResponse<any>> => {
    const params = new URLSearchParams();
    params.append('particular', particular);
    return apiCall<any>(`/code-master/by-particular?${params.toString()}`, { method: 'GET' });
  },
  getUniqueValues: async (field: string): Promise<ApiResponse<{ values: string[] }>> => {
    const params = new URLSearchParams();
    // Map frontend field names to backend field names
    const fieldMap: Record<string, string> = {
      'mainCategory': 'maincategory',
      'standardizedCode': 'maincategory', // Support old name for backward compatibility
    };
    const backendField = fieldMap[field] || field;
    params.append('field', backendField);
    return apiCall<{ values: string[] }>(`/code-master/unique-values?${params.toString()}`, { method: 'GET' });
  },
  create: async (payload: {
    RawParticulars: string;
    mainCategory: string;
    category1?: string;
    category2?: string;
    category3?: string;
    category4?: string;
    category5?: string;
  }): Promise<ApiResponse<any>> => {
    return apiCall<any>('/code-master', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  /**
   * Upload code master file
   */
  uploadFile: async (file: File, operationId?: string): Promise<ApiResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (operationId) {
      formData.append('operation_id', operationId);
    }
    
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      console.log('[CodeMaster Upload] Token found, setting Authorization header');
    } else {
      console.error('[CodeMaster Upload] No token found in localStorage!');
      throw new Error('Authentication token not found. Please login again.');
    }
    
    const url = `${API_BASE_URL}/code-master/upload`;
    console.log('[CodeMaster Upload] Sending request to:', url);
    console.log('[CodeMaster Upload] File:', file.name, file.size, 'bytes');
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });
    
    console.log('[CodeMaster Upload] Response status:', response.status);
    
    const data = await response.json();
    console.log('[CodeMaster Upload] Response data:', data);
    
    if (!response.ok) {
      const errorMsg = data.message || data.error || 'File upload failed';
      console.error('[CodeMaster Upload] Error:', errorMsg, data);
      throw new Error(errorMsg);
    }
    
    return data;
  },
  /**
   * Poll upload progress by operation id
   */
  getUploadProgress: async (operationId: string): Promise<ApiResponse<{ status: string; progress: number; message?: string; processed_rows?: number; total_rows?: number; meta?: any }>> => {
    return apiCall(`/code-master/upload/progress/${operationId}`, {
      method: 'GET',
    });
  },
  getById: async (codeId: number): Promise<ApiResponse<any>> => {
    return apiCall<any>(`/code-master/${codeId}`, { method: 'GET' });
  },
  update: async (codeId: number, payload: {
    RawParticulars: string;
    mainCategory: string;
    category1?: string;
    category2?: string;
    category3?: string;
    category4?: string;
    category5?: string;
  }): Promise<ApiResponse<any>> => {
    return apiCall<any>(`/code-master/${codeId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
  delete: async (codeId: number): Promise<ApiResponse<any>> => {
    return apiCall<any>(`/code-master/${codeId}`, {
      method: 'DELETE',
    });
  },
  deleteAll: async (): Promise<ApiResponse<{ deleted_count: number }>> => {
    return apiCall<{ deleted_count: number }>('/code-master/delete-all', {
      method: 'DELETE',
    });
  },
};

/**
 * Forex API calls
 */
export const forexApi = {
  /**
   * Get latest forex for a currency
   */
  get: async (currency: string) => {
    return apiCall<{
      currency: string;
      initial: { fx_id: number | null; rate: number | null; updated_at: string | null };
      latest: { fx_id: number | null; rate: number | null; month: string | null; updated_at: string | null };
    }>(`/forex/${encodeURIComponent(currency)}`, {
      method: 'GET',
    });
  },
  /**
   * List available currencies with initial/latest snapshots
   */
  list: async () => {
    return apiCall<{ items: Array<{
      currency: string;
      initial: { fx_id: number | null; rate: number | null; updated_at: string | null };
      latest: { fx_id: number | null; rate: number | null; month: string | null; updated_at: string | null };
    }> }>('/forex', { method: 'GET' });
  },
  /**
   * Update or insert forex for a currency
   * - latest_rate requires month
   * - initial_rate does not require month
   */
  update: async (currency: string, payload: { initial_rate?: number; latest_rate?: number; month?: string }) => {
    return apiCall(`/forex/${encodeURIComponent(currency)}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
  /**
   * Create a new forex row
   * - currency required
   * - latest_rate requires month
   * - at least one of initial_rate or latest_rate must be provided
   */
  create: async (payload: { currency: string; initial_rate?: number; latest_rate?: number; month?: string }) => {
    return apiCall('/forex', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  /**
   * Get FY-specific forex rates for an entity
   */
  getEntityFYRates: async (entityId: number, financialYear: number, currency?: string) => {
    const params = new URLSearchParams();
    if (currency) params.append('currency', currency);
    const queryString = params.toString();
    const endpoint = queryString 
      ? `/forex/entity/${entityId}/financial-year/${financialYear}?${queryString}`
      : `/forex/entity/${entityId}/financial-year/${financialYear}`;
    return apiCall<{
      entity_id: number;
      financial_year: number;
      rates: Array<{
        id: number;
        entity_id: number;
        currency: string;
        financial_year: number;
        opening_rate: number;
        closing_rate: number;
        fy_start_date: string;
        fy_end_date: string;
        created_at: string;
        updated_at: string;
      }>;
    }>(endpoint, { method: 'GET' });
  },
  /**
   * Set FY-specific forex rates for an entity
   */
  setEntityFYRates: async (entityId: number, financialYear: number, payload: {
    currency: string;
    opening_rate: number;
    closing_rate: number;
  }) => {
    return apiCall(`/forex/entity/${entityId}/financial-year/${financialYear}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  /**
   * Update FY-specific forex rates for an entity
   */
  updateEntityFYRates: async (entityId: number, financialYear: number, payload: {
    currency: string;
    opening_rate?: number;
    closing_rate?: number;
  }) => {
    return apiCall(`/forex/entity/${entityId}/financial-year/${financialYear}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
  /**
   * Get list of financial years with forex rates for an entity
   */
  getEntityFinancialYears: async (entityId: number) => {
    return apiCall<{
      entity_id: number;
      financial_years: number[];
    }>(`/forex/entity/${entityId}/financial-years`, { method: 'GET' });
  },
  /**
   * Get all forex rates for an entity across all financial years
   */
  getEntityAllRates: async (entityId: number) => {
    return apiCall<{
      entity_id: number;
      rates: Array<{
        id: number;
        entity_id: number;
        currency: string;
        financial_year: number;
        opening_rate: number;
        closing_rate: number;
        fy_start_date: string;
        fy_end_date: string;
        created_at: string;
        updated_at: string;
      }>;
    }>(`/forex/entity/${entityId}/rates`, { method: 'GET' });
  },
};

/**
 * Dashboard API calls
 */
export const dashboardApi = {
  /**
   * Get aggregated dashboard overview (KPIs + charts)
   */
  getOverview: async (entityId?: number, financialYear?: number, entityCode?: string) => {
    const params = new URLSearchParams();
    if (entityId) params.append('entity_id', entityId.toString());
    if (financialYear) params.append('financial_year', financialYear.toString());
    if (entityCode) params.append('entity_code', entityCode);

    const queryString = params.toString();
    const endpoint = queryString ? `/dashboard/overview?${queryString}` : '/dashboard/overview';

    return apiCall<{
      kpis: any;
      category_breakdown: any[];
      subcategory_breakdown: any[];
      entity_totals: any[];
      yearly_trend: any[];
      monthly_trend: any[];
      top_accounts: any[];
      bottom_accounts: any[];
      currency_mix: any[];
      fx_gaps: any[];
      unmapped: any[];
      pl_bs_mix: any[];
      concentration: any;
      variance_year: any[];
      variance_month: any[];
      alerts: string[];
    }>(endpoint, { method: 'GET' });
  },
};

/**
 * Reports API calls
 */
export const reportsApi = {
  /**
   * Get available metrics for reports
   */
  getMetrics: async () => {
    return apiCall<{ metrics: Array<{ value: string; label: string; category: string }> }>('/reports/metrics', {
      method: 'GET',
    });
  },

  /**
   * Get available financial years
   */
  getFinancialYears: async () => {
    return apiCall<{ years: Array<{ value: string; label: string; year: number }> }>('/reports/financial-years', {
      method: 'GET',
    });
  },

  /**
   * Get entities for reports
   */
  getEntities: async () => {
    return apiCall<{ entities: Array<{ ent_id: number; ent_name: string; ent_code: string }> }>('/reports/entities', {
      method: 'GET',
    });
  },

  /**
   * Get cross-entity comparison data
   */
  getComparison: async (metric?: string, financialYear?: number, entityIds?: number[]) => {
    const params = new URLSearchParams();
    if (metric) params.append('metric', metric);
    if (financialYear) params.append('financial_year', financialYear.toString());
    if (entityIds && entityIds.length > 0) {
      params.append('entity_ids', entityIds.join(','));
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/reports/comparison?${queryString}` : '/reports/comparison';

    return apiCall<{
      metric: string;
      financial_year: number | null;
      comparison_data: Array<{
        entity_code: string;
        entity_name: string;
        total_amount: number;
        total_amount_usd: number;
        record_count: number;
      }>;
      summary: {
        entity_count: number;
        total_amount: number;
        total_amount_usd: number;
        average_amount: number;
      };
    }>(endpoint, { method: 'GET' });
  },

  /**
   * Get alerts and red flags
   */
  getAlerts: async (financialYear?: number, entityId?: number, entityCode?: string) => {
    const params = new URLSearchParams();
    if (financialYear) params.append('financial_year', financialYear.toString());
    if (entityId) params.append('entity_id', entityId.toString());
    if (entityCode) params.append('entity_code', entityCode);

    const queryString = params.toString();
    const endpoint = queryString ? `/reports/alerts?${queryString}` : '/reports/alerts';

    return apiCall<{
      alerts: Array<{
        type: 'warning' | 'error' | 'info';
        severity: 'low' | 'medium' | 'high';
        entity_code: string;
        entity_name: string;
        title: string;
        message: string;
        metric: string;
        value: number;
      }>;
      count: number;
    }>(endpoint, { method: 'GET' });
  },

  /**
   * Export report
   */
  exportReport: async (metric?: string, financialYear?: number, entityIds?: number[]) => {
    const params = new URLSearchParams();
    if (metric) params.append('metric', metric);
    if (financialYear) params.append('financial_year', financialYear.toString());
    if (entityIds && entityIds.length > 0) {
      params.append('entity_ids', entityIds.join(','));
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/reports/export?${queryString}` : '/reports/export';

    return apiCall(endpoint, { method: 'GET' });
  },
};

/**
 * Financial Year Master API calls
 */
export const financialYearMasterApi = {
  /**
   * List all financial years, optionally filtered by is_active
   */
  list: async (isActive?: boolean): Promise<ApiResponse<{ financial_years: Array<{
    id: number;
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active: boolean;
    description: string | null;
    created_at: string;
    updated_at: string;
    created_by: number | null;
  }> }>> => {
    const params = new URLSearchParams();
    if (isActive !== undefined) params.append('is_active', isActive.toString());
    const queryString = params.toString();
    const endpoint = queryString ? `/financial-year-master?${queryString}` : '/financial-year-master';
    return apiCall<{ financial_years: Array<{
      id: number;
      financial_year: string;
      start_date: string;
      end_date: string;
      is_active: boolean;
      description: string | null;
      created_at: string;
      updated_at: string;
      created_by: number | null;
    }> }>(endpoint, { method: 'GET' });
  },

  /**
   * Get a single financial year by ID
   */
  get: async (id: number): Promise<ApiResponse<{
    id: number;
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active: boolean;
    description: string | null;
    created_at: string;
    updated_at: string;
    created_by: number | null;
  }>> => {
    return apiCall<{
      id: number;
      financial_year: string;
      start_date: string;
      end_date: string;
      is_active: boolean;
      description: string | null;
      created_at: string;
      updated_at: string;
      created_by: number | null;
    }>(`/financial-year-master/${id}`, { method: 'GET' });
  },

  /**
   * Create a new financial year
   */
  create: async (payload: {
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active?: boolean;
    description?: string;
  }): Promise<ApiResponse<{
    id: number;
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active: boolean;
    description: string | null;
    created_at: string;
    updated_at: string;
    created_by: number | null;
  }>> => {
    return apiCall<{
      id: number;
      financial_year: string;
      start_date: string;
      end_date: string;
      is_active: boolean;
      description: string | null;
      created_at: string;
      updated_at: string;
      created_by: number | null;
    }>('/financial-year-master', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update an existing financial year
   */
  update: async (id: number, payload: {
    financial_year?: string;
    start_date?: string;
    end_date?: string;
    is_active?: boolean;
    description?: string;
  }): Promise<ApiResponse<{
    id: number;
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active: boolean;
    description: string | null;
    created_at: string;
    updated_at: string;
    created_by: number | null;
  }>> => {
    return apiCall<{
      id: number;
      financial_year: string;
      start_date: string;
      end_date: string;
      is_active: boolean;
      description: string | null;
      created_at: string;
      updated_at: string;
      created_by: number | null;
    }>(`/financial-year-master/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Delete (deactivate) a financial year
   */
  delete: async (id: number): Promise<ApiResponse> => {
    return apiCall(`/financial-year-master/${id}`, { method: 'DELETE' });
  },

  /**
   * Validate if a date falls within any active financial year range
   */
  validate: async (date: string): Promise<ApiResponse<{
    valid: boolean;
    financial_year?: string;
    id?: number;
    message: string;
  }>> => {
    return apiCall<{
      valid: boolean;
      financial_year?: string;
      id?: number;
      message: string;
    }>(`/financial-year-master/validate?date=${encodeURIComponent(date)}`, {
      method: 'GET',
    });
  },

  /**
   * Get the current active financial year based on today's date
   */
  getCurrent: async (): Promise<ApiResponse<{
    financial_year: string;
    id: number;
    start_date: string;
    end_date: string;
  }>> => {
    return apiCall<{
      financial_year: string;
      id: number;
      start_date: string;
      end_date: string;
    }>('/financial-year-master/current', {
      method: 'GET',
    });
  },
};

export default {
  auth: authApi,
  test: testApi,
  upload: uploadApi,
  structuredData: structuredDataApi,
  entity: entityApi,
  codeMaster: codeMasterApi,
  forex: forexApi,
  dashboard: dashboardApi,
  reports: reportsApi,
  financialYearMaster: financialYearMasterApi,
};

