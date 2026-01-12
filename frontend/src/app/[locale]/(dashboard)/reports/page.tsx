'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';
import type {
  DashboardSummary,
  RevenueReport,
  OccupancyReport,
  PaymentReport,
  AgingReport,
} from '@/types';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Home,
  Users,
  FileText,
  Clock,
  RefreshCw,
} from 'lucide-react';

type ReportTab = 'overview' | 'revenue' | 'occupancy' | 'aging' | 'payments';

const paymentMethodLabels: Record<string, string> = {
  sinpe: 'Transferencia SINPE',
  sinpe_movil: 'SINPE Movil',
  credit_card: 'Tarjeta de Credito',
  cash: 'Efectivo',
  check: 'Cheque',
  bank_transfer: 'Transferencia Bancaria',
  other: 'Otro',
};

export default function ReportsPage() {
  const t = useTranslations('reports');
  const [activeTab, setActiveTab] = useState<ReportTab>('overview');
  const [loading, setLoading] = useState(true);

  // Report data
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [revenueReport, setRevenueReport] = useState<RevenueReport | null>(null);
  const [occupancyReport, setOccupancyReport] = useState<OccupancyReport | null>(null);
  const [agingReport, setAgingReport] = useState<AgingReport | null>(null);
  const [paymentReport, setPaymentReport] = useState<PaymentReport | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  async function loadReports() {
    setLoading(true);
    try {
      const [dashboardData, revenueData, occupancyData, agingData, paymentData] = await Promise.all([
        api.getDashboardSummary(),
        api.getRevenueReport({ group_by: 'month' }),
        api.getOccupancyReport(),
        api.getAgingReport(),
        api.getPaymentReport(),
      ]);

      setDashboard(dashboardData);
      setRevenueReport(revenueData);
      setOccupancyReport(occupancyData);
      setAgingReport(agingData);
      setPaymentReport(paymentData);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  }

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
          <p className="text-gray-600">Analisis y reportes de su negocio</p>
        </div>
        <Button variant="outline" onClick={loadReports}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-gray-200 pb-4">
        <Button
          variant={activeTab === 'overview' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('overview')}
        >
          <BarChart3 className="w-4 h-4 mr-2" />
          Resumen
        </Button>
        <Button
          variant={activeTab === 'revenue' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('revenue')}
        >
          <TrendingUp className="w-4 h-4 mr-2" />
          Ingresos
        </Button>
        <Button
          variant={activeTab === 'occupancy' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('occupancy')}
        >
          <Home className="w-4 h-4 mr-2" />
          Ocupacion
        </Button>
        <Button
          variant={activeTab === 'aging' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('aging')}
        >
          <Clock className="w-4 h-4 mr-2" />
          Antiguedad
        </Button>
        <Button
          variant={activeTab === 'payments' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setActiveTab('payments')}
        >
          <DollarSign className="w-4 h-4 mr-2" />
          Pagos
        </Button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && dashboard && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Ocupacion</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {dashboard.units.occupancy_rate}%
                    </p>
                  </div>
                  <div className="p-3 bg-primary-50 rounded-full">
                    <Home className="w-6 h-6 text-primary-600" />
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  {dashboard.units.occupied} de {dashboard.units.total} unidades
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Ingresos Esperados</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(dashboard.revenue.monthly_expected, 'CRC')}
                    </p>
                  </div>
                  <div className="p-3 bg-success-50 rounded-full">
                    <TrendingUp className="w-6 h-6 text-success-600" />
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-2">mensual</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Recaudado Este Mes</p>
                    <p className="text-2xl font-bold text-success-600">
                      {formatCurrency(dashboard.revenue.collected_this_month, 'CRC')}
                    </p>
                  </div>
                  <div className="p-3 bg-success-50 rounded-full">
                    <DollarSign className="w-6 h-6 text-success-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Por Cobrar</p>
                    <p className="text-2xl font-bold text-warning-600">
                      {formatCurrency(dashboard.revenue.total_outstanding, 'CRC')}
                    </p>
                  </div>
                  <div className="p-3 bg-warning-50 rounded-full">
                    <FileText className="w-6 h-6 text-warning-600" />
                  </div>
                </div>
                {dashboard.revenue.total_overdue > 0 && (
                  <p className="text-sm text-danger-600 mt-2">
                    {formatCurrency(dashboard.revenue.total_overdue, 'CRC')} vencido
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Home className="w-5 h-5" />
                  Unidades
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total</span>
                    <span className="font-medium">{dashboard.units.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Ocupadas</span>
                    <Badge variant="info">{dashboard.units.occupied}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Disponibles</span>
                    <Badge variant="success">{dashboard.units.available}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Mantenimiento</span>
                    <Badge variant="warning">{dashboard.units.maintenance}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Clientes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total</span>
                    <span className="font-medium">{dashboard.customers.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Activos</span>
                    <Badge variant="success">{dashboard.customers.active}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Contratos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total</span>
                    <span className="font-medium">{dashboard.contracts.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Activos</span>
                    <Badge variant="success">{dashboard.contracts.active}</Badge>
                  </div>
                  {dashboard.contracts.expiring_soon > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Por vencer (30 dias)</span>
                      <Badge variant="warning">{dashboard.contracts.expiring_soon}</Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Revenue Tab */}
      {activeTab === 'revenue' && revenueReport && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Total Facturado</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(revenueReport.totals.invoiced, 'CRC')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Total Recaudado</p>
                <p className="text-2xl font-bold text-success-600">
                  {formatCurrency(revenueReport.totals.collected, 'CRC')}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Tasa de Cobro</p>
                <p className="text-2xl font-bold text-primary-600">
                  {revenueReport.totals.collection_rate.toFixed(1)}%
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Ingresos por Periodo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {revenueReport.time_series.slice(-6).map((item) => (
                  <div key={item.period} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{item.period}</span>
                      <span className="font-medium">{formatCurrency(item.collected, 'CRC')}</span>
                    </div>
                    <div className="relative h-8 bg-gray-100 rounded overflow-hidden">
                      <div
                        className="absolute inset-y-0 left-0 bg-primary-200 rounded"
                        style={{
                          width: `${Math.min((item.invoiced / Math.max(...revenueReport.time_series.map(t => t.invoiced || 1))) * 100, 100)}%`,
                        }}
                      />
                      <div
                        className="absolute inset-y-0 left-0 bg-primary-600 rounded"
                        style={{
                          width: `${Math.min((item.collected / Math.max(...revenueReport.time_series.map(t => t.invoiced || 1))) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-4 mt-6 pt-4 border-t text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-primary-200 rounded" />
                  <span>Facturado</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-primary-600 rounded" />
                  <span>Recaudado</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Occupancy Tab */}
      {activeTab === 'occupancy' && occupancyReport && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Ocupacion General</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-8">
                <div className="relative w-32 h-32">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="64" cy="64" r="56" stroke="#e5e7eb" strokeWidth="16" fill="none" />
                    <circle
                      cx="64" cy="64" r="56"
                      stroke="#4f46e5" strokeWidth="16" fill="none"
                      strokeLinecap="round"
                      strokeDasharray={`${occupancyReport.overall.occupancy_rate * 3.52} 352`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold">{occupancyReport.overall.occupancy_rate}%</span>
                  </div>
                </div>
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Unidades</p>
                    <p className="text-xl font-bold">{occupancyReport.overall.total_units}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Ocupadas</p>
                    <p className="text-xl font-bold text-primary-600">{occupancyReport.overall.occupied}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Disponibles</p>
                    <p className="text-xl font-bold text-success-600">{occupancyReport.overall.available}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Mantenimiento</p>
                    <p className="text-xl font-bold text-warning-600">{occupancyReport.overall.maintenance}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Ocupacion por Tipo de Unidad</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ocupadas</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Disponibles</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ocupacion</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {occupancyReport.by_type.map((item) => (
                      <tr key={item.type}>
                        <td className="px-4 py-3 font-medium capitalize">{item.type.replace('_', ' ')}</td>
                        <td className="px-4 py-3 text-right">{item.total}</td>
                        <td className="px-4 py-3 text-right">{item.occupied}</td>
                        <td className="px-4 py-3 text-right">{item.available}</td>
                        <td className="px-4 py-3 text-right">
                          <Badge variant={item.occupancy_rate >= 80 ? 'success' : item.occupancy_rate >= 50 ? 'warning' : 'default'}>
                            {item.occupancy_rate}%
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Aging Tab */}
      {activeTab === 'aging' && agingReport && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Total Por Cobrar</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(agingReport.total_outstanding, 'CRC')}
                </p>
                <p className="text-sm text-gray-500 mt-1">{agingReport.total_invoices} facturas pendientes</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Al dia de</p>
                <p className="text-2xl font-bold text-gray-900">
                  {new Date(agingReport.as_of_date).toLocaleDateString('es-CR')}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Antiguedad de Cuentas por Cobrar</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {agingReport.aging_summary.map((bucket) => (
                  <div key={bucket.bucket} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{bucket.bucket}</span>
                        <Badge variant={
                          bucket.bucket === 'Vigente' ? 'success' :
                          bucket.bucket === '1-30 dias' ? 'warning' : 'error'
                        }>
                          {bucket.count} facturas
                        </Badge>
                      </div>
                      <span className="text-lg font-bold">{formatCurrency(bucket.amount, 'CRC')}</span>
                    </div>
                    {bucket.invoices.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-gray-500">
                              <th className="text-left pb-2">Factura</th>
                              <th className="text-left pb-2">Cliente</th>
                              <th className="text-right pb-2">Monto</th>
                              <th className="text-right pb-2">Dias</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {bucket.invoices.slice(0, 5).map((inv) => (
                              <tr key={inv.invoice_number}>
                                <td className="py-2">{inv.invoice_number}</td>
                                <td className="py-2">{inv.customer_name}</td>
                                <td className="py-2 text-right">{formatCurrency(inv.amount, 'CRC')}</td>
                                <td className="py-2 text-right">
                                  {inv.days_outstanding > 0 ? `+${inv.days_outstanding}` : inv.days_outstanding}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Payments Tab */}
      {activeTab === 'payments' && paymentReport && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Total Pagos</p>
                <p className="text-2xl font-bold text-gray-900">{paymentReport.total_payments}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600">Monto Total</p>
                <p className="text-2xl font-bold text-success-600">
                  {formatCurrency(paymentReport.total_amount, 'CRC')}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Pagos por Metodo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {paymentReport.by_method.map((item) => (
                  <div key={item.method} className="flex items-center gap-4">
                    <div className="w-32 font-medium">
                      {paymentMethodLabels[item.method] || item.method}
                    </div>
                    <div className="flex-1">
                      <div className="h-8 bg-gray-100 rounded overflow-hidden">
                        <div
                          className="h-full bg-primary-600 rounded flex items-center justify-end px-2"
                          style={{ width: `${Math.max(item.percentage, 5)}%` }}
                        >
                          {item.percentage >= 10 && (
                            <span className="text-xs text-white font-medium">{item.percentage.toFixed(0)}%</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="w-24 text-right">
                      <p className="font-medium">{formatCurrency(item.amount, 'CRC')}</p>
                      <p className="text-xs text-gray-500">{item.count} pagos</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
