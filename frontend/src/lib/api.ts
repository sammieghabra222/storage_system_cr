import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
  AuthResponse,
  User,
  Tenant,
  StorageUnit,
  StorageUnitStats,
  Customer,
  Contract,
  Invoice,
  InvoiceSummary,
  Payment,
  PaymentSummary,
  PaginatedResponse,
  DashboardSummary,
  RevenueReport,
  OccupancyReport,
  PaymentReport,
  AgingReport,
  CustomerReport,
  SupportedCurrency,
  ExchangeRateResponse,
  CurrencyRateResponse,
  CurrencyConversionResponse,
  FormattedCurrencyResponse,
  CardPaymentIntent,
  CardPaymentStatus,
  CardRefundResult,
  SinpeQRResponse,
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth header
    this.client.interceptors.request.use((config) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    // Response interceptor for token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && this.refreshToken && originalRequest) {
          try {
            const response = await this.refreshAccessToken();
            this.setTokens(response.access_token, response.refresh_token);
            originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;
            return this.client(originalRequest);
          } catch {
            this.clearTokens();
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );

    // Load tokens from localStorage
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('accessToken');
      this.refreshToken = localStorage.getItem('refreshToken');
    }
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', { email, password });
    this.setTokens(response.data.tokens.access_token, response.data.tokens.refresh_token);
    return response.data;
  }

  async register(data: {
    business_name: string;
    business_email: string;
    business_phone?: string;
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    locale?: string;
  }): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/register', data);
    this.setTokens(response.data.tokens.access_token, response.data.tokens.refresh_token);
    return response.data;
  }

  async refreshAccessToken(): Promise<{ access_token: string; refresh_token: string }> {
    const response = await this.client.post('/auth/refresh', { refresh_token: this.refreshToken });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  logout() {
    this.clearTokens();
  }

  // Tenant endpoints
  async getCurrentTenant(): Promise<Tenant> {
    const response = await this.client.get<Tenant>('/tenants/current');
    return response.data;
  }

  async updateTenant(data: Partial<Tenant>): Promise<Tenant> {
    const response = await this.client.patch<Tenant>('/tenants/current', data);
    return response.data;
  }

  // Storage Units endpoints
  async getStorageUnits(params?: { skip?: number; limit?: number; status?: string }): Promise<PaginatedResponse<StorageUnit>> {
    const response = await this.client.get<PaginatedResponse<StorageUnit>>('/units', { params });
    return response.data;
  }

  async getStorageUnitStats(): Promise<StorageUnitStats> {
    const response = await this.client.get<StorageUnitStats>('/units/stats');
    return response.data;
  }

  async getAvailableUnits(): Promise<StorageUnit[]> {
    const response = await this.client.get<StorageUnit[]>('/units/available');
    return response.data;
  }

  async getStorageUnit(id: string): Promise<StorageUnit> {
    const response = await this.client.get<StorageUnit>(`/units/${id}`);
    return response.data;
  }

  async createStorageUnit(data: Partial<StorageUnit>): Promise<StorageUnit> {
    const response = await this.client.post<StorageUnit>('/units', data);
    return response.data;
  }

  async updateStorageUnit(id: string, data: Partial<StorageUnit>): Promise<StorageUnit> {
    const response = await this.client.patch<StorageUnit>(`/units/${id}`, data);
    return response.data;
  }

  async deleteStorageUnit(id: string): Promise<void> {
    await this.client.delete(`/units/${id}`);
  }

  // Customer endpoints
  async getCustomers(params?: { skip?: number; limit?: number; search?: string }): Promise<PaginatedResponse<Customer>> {
    const response = await this.client.get<PaginatedResponse<Customer>>('/customers', { params });
    return response.data;
  }

  async getCustomer(id: string): Promise<Customer> {
    const response = await this.client.get<Customer>(`/customers/${id}`);
    return response.data;
  }

  async createCustomer(data: Partial<Customer>): Promise<Customer> {
    const response = await this.client.post<Customer>('/customers', data);
    return response.data;
  }

  async updateCustomer(id: string, data: Partial<Customer>): Promise<Customer> {
    const response = await this.client.patch<Customer>(`/customers/${id}`, data);
    return response.data;
  }

  async deleteCustomer(id: string): Promise<void> {
    await this.client.delete(`/customers/${id}`);
  }

  // Contract endpoints
  async getContracts(params?: { skip?: number; limit?: number; status?: string; customer_id?: string }): Promise<PaginatedResponse<Contract>> {
    const response = await this.client.get<PaginatedResponse<Contract>>('/contracts', { params });
    return response.data;
  }

  async getContract(id: string): Promise<Contract> {
    const response = await this.client.get<Contract>(`/contracts/${id}`);
    return response.data;
  }

  async createContract(data: Partial<Contract>): Promise<Contract> {
    const response = await this.client.post<Contract>('/contracts', data);
    return response.data;
  }

  async updateContract(id: string, data: Partial<Contract>): Promise<Contract> {
    const response = await this.client.patch<Contract>(`/contracts/${id}`, data);
    return response.data;
  }

  async processMoveIn(id: string, data: { move_in_date: string; deposit_paid: boolean; access_code?: string }): Promise<Contract> {
    const response = await this.client.post<Contract>(`/contracts/${id}/move-in`, data);
    return response.data;
  }

  async processMoveOut(id: string, data: { move_out_date: string; return_deposit: boolean; notes?: string }): Promise<Contract> {
    const response = await this.client.post<Contract>(`/contracts/${id}/move-out`, data);
    return response.data;
  }

  // Invoice endpoints
  async getInvoices(params?: { skip?: number; limit?: number; status?: string; customer_id?: string; overdue_only?: boolean }): Promise<PaginatedResponse<Invoice>> {
    const response = await this.client.get<PaginatedResponse<Invoice>>('/invoices', { params });
    return response.data;
  }

  async getInvoiceSummary(): Promise<InvoiceSummary> {
    const response = await this.client.get<InvoiceSummary>('/invoices/summary');
    return response.data;
  }

  async getInvoice(id: string): Promise<Invoice> {
    const response = await this.client.get<Invoice>(`/invoices/${id}`);
    return response.data;
  }

  async createInvoice(data: Partial<Invoice>): Promise<Invoice> {
    const response = await this.client.post<Invoice>('/invoices', data);
    return response.data;
  }

  async updateInvoice(id: string, data: Partial<Invoice>): Promise<Invoice> {
    const response = await this.client.patch<Invoice>(`/invoices/${id}`, data);
    return response.data;
  }

  async sendInvoice(id: string): Promise<Invoice> {
    const response = await this.client.post<Invoice>(`/invoices/${id}/send`);
    return response.data;
  }

  async cancelInvoice(id: string): Promise<Invoice> {
    const response = await this.client.post<Invoice>(`/invoices/${id}/cancel`);
    return response.data;
  }

  // Payment endpoints
  async getPayments(params?: { skip?: number; limit?: number; customer_id?: string; pending_only?: boolean }): Promise<PaginatedResponse<Payment>> {
    const response = await this.client.get<PaginatedResponse<Payment>>('/payments', { params });
    return response.data;
  }

  async getPaymentSummary(): Promise<PaymentSummary> {
    const response = await this.client.get<PaymentSummary>('/payments/summary');
    return response.data;
  }

  async getPendingPayments(): Promise<Payment[]> {
    const response = await this.client.get<Payment[]>('/payments/pending');
    return response.data;
  }

  async getPayment(id: string): Promise<Payment> {
    const response = await this.client.get<Payment>(`/payments/${id}`);
    return response.data;
  }

  async recordPayment(data: Partial<Payment>): Promise<Payment> {
    const response = await this.client.post<Payment>('/payments', data);
    return response.data;
  }

  async recordSinpePayment(data: {
    customer_id: string;
    invoice_id?: string;
    amount: number;
    sinpe_phone?: string;
    sinpe_confirmation?: string;
    notes?: string;
  }): Promise<Payment> {
    const response = await this.client.post<Payment>('/payments/sinpe', data);
    return response.data;
  }

  async confirmPayment(id: string, data: { reference_number?: string; sinpe_confirmation?: string; notes?: string }): Promise<Payment> {
    const response = await this.client.post<Payment>(`/payments/${id}/confirm`, data);
    return response.data;
  }

  async rejectPayment(id: string, reason?: string): Promise<Payment> {
    const response = await this.client.post<Payment>(`/payments/${id}/reject`, null, { params: { reason } });
    return response.data;
  }

  // Card Payment endpoints
  async createCardPaymentIntent(data: {
    customer_id: string;
    invoice_id?: string;
    amount: number;
    currency?: string;
    description?: string;
  }): Promise<CardPaymentIntent> {
    const response = await this.client.post<CardPaymentIntent>('/payments/card/intent', data);
    return response.data;
  }

  async confirmCardPayment(data: {
    intent_id: string;
    payment_method_id?: string;
  }): Promise<CardPaymentStatus> {
    const response = await this.client.post<CardPaymentStatus>('/payments/card/confirm', data);
    return response.data;
  }

  async getCardPaymentStatus(intentId: string): Promise<CardPaymentStatus> {
    const response = await this.client.get<CardPaymentStatus>(`/payments/card/status/${intentId}`);
    return response.data;
  }

  async refundCardPayment(data: {
    transaction_id: string;
    amount?: number;
    reason?: string;
  }): Promise<CardRefundResult> {
    const response = await this.client.post<CardRefundResult>('/payments/card/refund', data);
    return response.data;
  }

  async cancelCardPayment(intentId: string): Promise<CardPaymentStatus> {
    const response = await this.client.post<CardPaymentStatus>(`/payments/card/cancel/${intentId}`);
    return response.data;
  }

  // SINPE QR endpoints
  async generateSinpeQR(data: {
    amount: number;
    invoice_id?: string;
    description?: string;
  }): Promise<SinpeQRResponse> {
    const response = await this.client.post<SinpeQRResponse>('/payments/sinpe/qr', data);
    return response.data;
  }

  async generateInvoiceSinpeQR(invoiceId: string): Promise<SinpeQRResponse> {
    const response = await this.client.get<SinpeQRResponse>(`/payments/sinpe/qr/invoice/${invoiceId}`);
    return response.data;
  }

  // Analytics endpoints
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await this.client.get<DashboardSummary>('/analytics/dashboard');
    return response.data;
  }

  async getRevenueReport(params?: { start_date?: string; end_date?: string; group_by?: string }): Promise<RevenueReport> {
    const response = await this.client.get<RevenueReport>('/analytics/revenue', { params });
    return response.data;
  }

  async getOccupancyReport(): Promise<OccupancyReport> {
    const response = await this.client.get<OccupancyReport>('/analytics/occupancy');
    return response.data;
  }

  async getPaymentReport(params?: { start_date?: string; end_date?: string }): Promise<PaymentReport> {
    const response = await this.client.get<PaymentReport>('/analytics/payments', { params });
    return response.data;
  }

  async getAgingReport(): Promise<AgingReport> {
    const response = await this.client.get<AgingReport>('/analytics/aging');
    return response.data;
  }

  async getCustomerReport(): Promise<CustomerReport> {
    const response = await this.client.get<CustomerReport>('/analytics/customers');
    return response.data;
  }

  // Exchange Rate endpoints
  async getCurrentExchangeRates(): Promise<ExchangeRateResponse> {
    const response = await this.client.get<ExchangeRateResponse>('/exchange-rates/current');
    return response.data;
  }

  async getUsdRate(params?: { rate_date?: string; rate_type?: 'buy' | 'sell' }): Promise<CurrencyRateResponse> {
    const response = await this.client.get<CurrencyRateResponse>('/exchange-rates/usd', { params });
    return response.data;
  }

  async getEurRate(params?: { rate_date?: string; rate_type?: 'buy' | 'sell' }): Promise<CurrencyRateResponse> {
    const response = await this.client.get<CurrencyRateResponse>('/exchange-rates/eur', { params });
    return response.data;
  }

  async convertCurrency(params: {
    amount: number;
    from_currency: SupportedCurrency;
    to_currency?: SupportedCurrency;
    rate_date?: string;
  }): Promise<CurrencyConversionResponse> {
    const response = await this.client.post<CurrencyConversionResponse>('/exchange-rates/convert', null, { params });
    return response.data;
  }

  async formatCurrency(params: {
    amount: number;
    currency?: SupportedCurrency;
    locale?: 'es' | 'en';
  }): Promise<FormattedCurrencyResponse> {
    const response = await this.client.get<FormattedCurrencyResponse>('/exchange-rates/format', { params });
    return response.data;
  }
}

// Export singleton instance
export const api = new ApiClient();
