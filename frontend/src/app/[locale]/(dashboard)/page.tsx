'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useAuthStore } from '@/stores/auth';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils';
import { DonutChart, BarChart, AreaChart, StatsCard, MetricCard } from '@/components/charts';
import type { StorageUnitStats, InvoiceSummary, PaymentSummary, DashboardSummary, RevenueReport } from '@/types';
import {
  Package,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  CreditCard,
  FileText,
  Users,
  ArrowRight,
  DollarSign,
  Calendar,
} from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const t = useTranslations('dashboard');
  const tCommon = useTranslations('common');
  const { user, tenant } = useAuthStore();
  const [unitStats, setUnitStats] = useState<StorageUnitStats | null>(null);
  const [invoiceSummary, setInvoiceSummary] = useState<InvoiceSummary | null>(null);
  const [paymentSummary, setPaymentSummary] = useState<PaymentSummary | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [revenueData, setRevenueData] = useState<RevenueReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [units, invoices, payments, dashboard, revenue] = await Promise.all([
          api.getStorageUnitStats(),
          api.getInvoiceSummary(),
          api.getPaymentSummary(),
          api.getDashboardSummary().catch(() => null),
          api.getRevenueReport({ group_by: 'month' }).catch(() => null),
        ]);
        setUnitStats(units);
        setInvoiceSummary(invoices);
        setPaymentSummary(payments);
        setDashboardData(dashboard);
        setRevenueData(revenue);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  const currency = tenant?.currency || 'CRC';

  // Prepare occupancy chart data
  const occupancyChartData = unitStats
    ? [
        { label: t('occupiedUnits'), value: unitStats.occupied, color: '#10b981' },
        { label: t('availableUnits'), value: unitStats.available, color: '#3b82f6' },
        { label: 'Mantenimiento', value: unitStats.maintenance, color: '#f59e0b' },
      ]
    : [];

  // Prepare payment methods chart data
  const paymentMethodsData = paymentSummary?.by_method
    ? Object.entries(paymentSummary.by_method).map(([method, data]) => ({
        label: method.toUpperCase(),
        value: data.amount,
      }))
    : [];

  // Prepare revenue trend data
  const revenueTrendData = revenueData?.time_series?.slice(-6).map((item) => ({
    label: item.period.slice(-2), // Last 2 chars (month)
    value: item.collected,
  })) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
          <p className="text-gray-600">
            {t('welcome', { name: user?.first_name || 'Usuario' })}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/es/reports"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
          >
            {t('viewReports')}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          label={t('occupancyRate')}
          value={`${unitStats?.occupancy_rate || 0}%`}
          icon={TrendingUp}
          color="success"
          trend={{ value: 2.5, label: 'vs mes anterior' }}
        />
        <StatsCard
          label={t('totalUnits')}
          value={unitStats?.total || 0}
          icon={Package}
          color="primary"
        />
        <StatsCard
          label={t('monthlyRevenue')}
          value={formatCurrency(paymentSummary?.confirmed_amount || 0, currency)}
          icon={DollarSign}
          color="success"
        />
        <StatsCard
          label={t('overdueInvoices')}
          value={invoiceSummary?.overdue_count || 0}
          icon={AlertCircle}
          color={invoiceSummary?.overdue_count ? 'danger' : 'gray'}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Occupancy Donut Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t('occupancyRate')}</CardTitle>
          </CardHeader>
          <CardContent>
            {unitStats && unitStats.total > 0 ? (
              <DonutChart
                data={occupancyChartData}
                size={140}
                thickness={20}
                centerValue={`${unitStats.occupancy_rate}%`}
                centerLabel="Ocupado"
              />
            ) : (
              <div className="flex items-center justify-center h-40 text-gray-400">
                No hay datos
              </div>
            )}
          </CardContent>
        </Card>

        {/* Revenue Trend */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">{t('monthlyRevenue')}</CardTitle>
            <Link
              href="/es/reports?tab=revenue"
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Ver detalle
            </Link>
          </CardHeader>
          <CardContent>
            {revenueTrendData.length > 0 ? (
              <AreaChart
                data={revenueTrendData}
                height={180}
                color="#10b981"
                showDots
                showLabels
                formatValue={(v) => formatCurrency(v, currency)}
              />
            ) : (
              <div className="flex items-center justify-center h-44 text-gray-400">
                No hay datos de ingresos
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Resumen de Pagos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-xs text-green-600 font-medium">Confirmados</p>
                <p className="text-xl font-bold text-green-700">
                  {paymentSummary?.confirmed_count || 0}
                </p>
                <p className="text-sm text-green-600">
                  {formatCurrency(paymentSummary?.confirmed_amount || 0, currency)}
                </p>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-xs text-amber-600 font-medium">Pendientes</p>
                <p className="text-xl font-bold text-amber-700">
                  {paymentSummary?.pending_count || 0}
                </p>
                <p className="text-sm text-amber-600">
                  {formatCurrency(paymentSummary?.pending_amount || 0, currency)}
                </p>
              </div>
            </div>

            {paymentMethodsData.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Por Metodo de Pago</p>
                <BarChart
                  data={paymentMethodsData}
                  horizontal
                  formatValue={(v) => formatCurrency(v, currency)}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions & SINPE */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t('quickActions')}</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              <Link
                href="/es/contracts?action=add"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-200 transition-colors"
              >
                <FileText className="w-5 h-5 text-primary-600" />
                <span className="text-sm font-medium">{t('newContract')}</span>
              </Link>
              <Link
                href="/es/payments?action=add"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-200 transition-colors"
              >
                <CreditCard className="w-5 h-5 text-primary-600" />
                <span className="text-sm font-medium">{t('newPayment')}</span>
              </Link>
              <Link
                href="/es/customers?action=add"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-200 transition-colors"
              >
                <Users className="w-5 h-5 text-primary-600" />
                <span className="text-sm font-medium">Nuevo Cliente</span>
              </Link>
              <Link
                href="/es/invoices?action=add"
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-primary-200 transition-colors"
              >
                <FileText className="w-5 h-5 text-primary-600" />
                <span className="text-sm font-medium">Nueva Factura</span>
              </Link>
            </CardContent>
          </Card>

          {/* SINPE Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">SINPE Movil</CardTitle>
            </CardHeader>
            <CardContent>
              {tenant?.sinpe_number ? (
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">
                    Numero para recibir pagos:
                  </p>
                  <div className="p-4 bg-primary-50 rounded-lg text-center">
                    <p className="text-2xl font-mono font-bold text-primary-600">
                      {tenant.sinpe_number}
                    </p>
                  </div>
                  <p className="text-xs text-gray-500 text-center">
                    Comparta este numero con sus clientes
                  </p>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-sm text-gray-600 mb-3">
                    Configure su numero SINPE
                  </p>
                  <Link
                    href="/es/settings"
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    Ir a Configuracion
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">{t('totalCustomers')}</p>
              <p className="text-lg font-semibold text-gray-900">
                {dashboardData?.customers?.total || '-'}
              </p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-xs text-gray-500">{t('activeContracts')}</p>
              <p className="text-lg font-semibold text-gray-900">
                {dashboardData?.contracts?.active || '-'}
              </p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-amber-500" />
            <div>
              <p className="text-xs text-gray-500">{t('expiringContracts')}</p>
              <p className="text-lg font-semibold text-gray-900">
                {dashboardData?.contracts?.expiring_soon || '-'}
              </p>
            </div>
          </div>
        </div>
        <div className="p-4 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <div>
              <p className="text-xs text-gray-500">{t('overdueAmount')}</p>
              <p className="text-lg font-semibold text-gray-900">
                {dashboardData?.revenue?.total_overdue
                  ? formatCurrency(dashboardData.revenue.total_overdue, currency)
                  : '-'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
