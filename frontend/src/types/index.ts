// API Types for the storage management platform

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'owner' | 'manager' | 'staff' | 'viewer';
  tenant_id: string;
  locale: string;
}

export interface Tenant {
  id: string;
  name: string;
  legal_name: string | null;
  cedula_juridica: string | null;
  email: string;
  phone: string | null;
  address: string | null;
  city: string | null;
  province: string | null;
  postal_code: string | null;
  country: string;
  currency: string;
  timezone: string;
  locale: string;
  sinpe_number: string | null;
  is_active: boolean;
}

export interface StorageUnit {
  id: string;
  unit_number: string;
  unit_type: 'standard' | 'climate_controlled' | 'vehicle' | 'locker' | 'outdoor';
  status: 'available' | 'occupied' | 'reserved' | 'maintenance' | 'unavailable';
  width: number | null;
  length: number | null;
  height: number | null;
  monthly_rate: number;
  deposit_amount: number | null;
  floor: number | null;
  building: string | null;
  zone: string | null;
  has_electricity: boolean;
  has_climate_control: boolean;
  is_drive_up: boolean;
  is_indoor: boolean;
  notes: string | null;
  current_customer_id: string | null;
  current_contract_id: string | null;
  area_sqm: number | null;
  volume_cbm: number | null;
}

export interface Customer {
  id: string;
  customer_type: 'individual' | 'business';
  cedula: string | null;
  cedula_juridica: string | null;
  first_name: string;
  last_name: string | null;
  company_name: string | null;
  display_name: string;
  email: string;
  phone: string;
  phone_secondary: string | null;
  address: string | null;
  city: string | null;
  province: string | null;
  postal_code: string | null;
  country: string;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  preferred_language: string;
  accepts_email_notifications: boolean;
  accepts_sms_notifications: boolean;
  is_active: boolean;
  notes: string | null;
}

export interface Contract {
  id: string;
  contract_number: string;
  customer_id: string;
  unit_id: string;
  status: 'draft' | 'active' | 'expired' | 'terminated' | 'suspended';
  start_date: string;
  end_date: string | null;
  signed_date: string | null;
  move_in_date: string | null;
  move_out_date: string | null;
  monthly_rate: number;
  effective_monthly_rate: number;
  deposit_amount: number;
  deposit_paid: boolean;
  deposit_returned: boolean;
  billing_cycle: 'monthly' | 'quarterly' | 'semi_annual' | 'annual';
  billing_day: number;
  grace_period_days: number;
  late_fee_amount: number;
  late_fee_percent: number | null;
  auto_renew: boolean;
  renewal_notice_days: number;
  discount_percent: number | null;
  discount_reason: string | null;
  requires_insurance: boolean;
  insurance_provider: string | null;
  access_code: string | null;
  access_hours: string | null;
  is_month_to_month: boolean;
  special_terms: string | null;
  internal_notes: string | null;
}

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent: number;
  subtotal: number;
  tax_amount: number;
  total: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  customer_id: string;
  contract_id: string | null;
  status: 'draft' | 'sent' | 'viewed' | 'partial' | 'paid' | 'overdue' | 'cancelled' | 'refunded';
  issue_date: string;
  due_date: string;
  period_start: string | null;
  period_end: string | null;
  line_items: InvoiceLineItem[];
  subtotal: number;
  tax_total: number;
  discount_total: number;
  total: number;
  amount_paid: number;
  balance_due: number;
  currency: string;
  late_fee_applied: boolean;
  late_fee_amount: number;
  is_overdue: boolean;
  hacienda_key: string | null;
  hacienda_status: string | null;
  notes: string | null;
}

export interface Payment {
  id: string;
  payment_number: string;
  customer_id: string;
  invoice_id: string | null;
  method: 'sinpe' | 'sinpe_movil' | 'credit_card' | 'debit_card' | 'cash' | 'check' | 'bank_transfer' | 'other';
  status: 'pending' | 'confirmed' | 'failed' | 'refunded' | 'cancelled';
  amount: number;
  currency: string;
  payment_date: string;
  confirmed_at: string | null;
  confirmed_by: string | null;
  reference_number: string | null;
  transaction_id: string | null;
  sinpe_phone: string | null;
  sinpe_confirmation: string | null;
  card_last_four: string | null;
  card_brand: string | null;
  processing_fee: number;
  net_amount: number;
  notes: string | null;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface AuthResponse {
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
  user: User;
}

export interface StorageUnitStats {
  total: number;
  available: number;
  occupied: number;
  reserved: number;
  maintenance: number;
  occupancy_rate: number;
}

export interface InvoiceSummary {
  total_invoices: number;
  total_amount: number;
  total_paid: number;
  total_outstanding: number;
  overdue_count: number;
  overdue_amount: number;
}

export interface PaymentSummary {
  total_payments: number;
  total_amount: number;
  pending_count: number;
  pending_amount: number;
  confirmed_count: number;
  confirmed_amount: number;
  by_method: Record<string, { count: number; amount: number }>;
}

// Analytics Types
export interface DashboardSummary {
  units: {
    total: number;
    occupied: number;
    available: number;
    maintenance: number;
    occupancy_rate: number;
  };
  customers: {
    total: number;
    active: number;
  };
  contracts: {
    total: number;
    active: number;
    expiring_soon: number;
  };
  revenue: {
    monthly_expected: number;
    collected_this_month: number;
    total_outstanding: number;
    total_overdue: number;
  };
  invoices: {
    pending_count: number;
    overdue_count: number;
  };
}

export interface RevenueReport {
  start_date: string;
  end_date: string;
  group_by: string;
  time_series: Array<{
    period: string;
    invoiced: number;
    collected: number;
  }>;
  totals: {
    invoiced: number;
    collected: number;
    collection_rate: number;
  };
}

export interface OccupancyReport {
  overall: {
    total_units: number;
    occupied: number;
    available: number;
    maintenance: number;
    occupancy_rate: number;
  };
  by_type: Array<{
    type: string;
    total: number;
    occupied: number;
    available: number;
    occupancy_rate: number;
  }>;
  by_building: Array<{
    building: string;
    total: number;
    occupied: number;
    available: number;
    occupancy_rate: number;
  }>;
}

export interface PaymentReport {
  start_date: string;
  end_date: string;
  total_payments: number;
  total_amount: number;
  by_method: Array<{
    method: string;
    count: number;
    amount: number;
    percentage: number;
  }>;
}

export interface AgingReport {
  as_of_date: string;
  total_outstanding: number;
  total_invoices: number;
  aging_summary: Array<{
    bucket: string;
    count: number;
    amount: number;
    invoices: Array<{
      invoice_number: string;
      customer_name: string;
      due_date: string;
      amount: number;
      days_outstanding: number;
    }>;
  }>;
}

export interface CustomerReport {
  summary: {
    total: number;
    active: number;
    inactive: number;
    individual: number;
    business: number;
  };
  top_customers: Array<{
    id: string;
    name: string;
    type: string;
    active_contracts: number;
    total_revenue: number;
    is_active: boolean;
  }>;
  all_customers: Array<{
    id: string;
    name: string;
    type: string;
    active_contracts: number;
    total_revenue: number;
    is_active: boolean;
  }>;
}

// Currency Types
export type SupportedCurrency = 'CRC' | 'USD' | 'EUR';

export interface ExchangeRateResponse {
  date: string;
  base_currency: string;
  rates: {
    USD?: { buy: number; sell: number };
    EUR?: { buy: number; sell: number };
  };
  source: string;
}

export interface CurrencyRateResponse {
  currency: string;
  base_currency: string;
  rate: number | null;
  rate_type: 'buy' | 'sell';
  date: string;
  source: string;
}

export interface CurrencyConversionResponse {
  original_amount: number;
  original_currency: SupportedCurrency;
  converted_amount: number;
  converted_currency: SupportedCurrency;
  exchange_rate: {
    from_to_crc: number;
    crc_to_target: number | null;
  };
  date: string;
  source: string;
}

export interface FormattedCurrencyResponse {
  amount: string;
  currency: SupportedCurrency;
  formatted: string;
  locale: string;
}

// Card Payment Types
export interface CardPaymentIntent {
  intent_id: string;
  client_secret: string | null;
  status: string;
  amount: number;
  currency: string;
}

export interface CardPaymentStatus {
  intent_id: string;
  status: string;
  success: boolean;
  transaction_id: string | null;
  card_brand: string | null;
  card_last_four: string | null;
  amount_captured: number | null;
  processing_fee: number | null;
  error_message: string | null;
}

export interface CardRefundResult {
  success: boolean;
  refund_id: string | null;
  amount_refunded: number;
  status: string;
  error_message: string | null;
}

// SINPE QR Types
export interface SinpeQRResponse {
  qr_data: string;
  phone_number: string;
  recipient_name: string;
  amount: number | null;
  currency: string;
  description: string | null;
  invoice_number: string | null;
  qr_base64: string | null;
}
