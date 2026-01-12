'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge, getStatusBadgeVariant } from '@/components/ui/badge';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Alert } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency } from '@/lib/utils';
import type { Payment, PaymentSummary, Customer, Invoice, Tenant } from '@/types';
import {
  Plus,
  CreditCard,
  Smartphone,
  Check,
  X,
  Eye,
  Clock,
  CheckCircle,
  DollarSign,
  AlertTriangle,
  Phone,
  Hash,
  Calendar,
  User,
  FileText,
} from 'lucide-react';

type PaymentFilter = 'all' | 'pending' | 'confirmed' | 'failed';

const paymentMethodLabels: Record<string, string> = {
  sinpe: 'Transferencia SINPE',
  sinpe_movil: 'SINPE Movil',
  credit_card: 'Tarjeta de Credito',
  debit_card: 'Tarjeta de Debito',
  cash: 'Efectivo',
  check: 'Cheque',
  bank_transfer: 'Transferencia Bancaria',
  other: 'Otro',
};

const paymentStatusLabels: Record<string, string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmado',
  failed: 'Fallido',
  refunded: 'Reembolsado',
  cancelled: 'Cancelado',
};

export default function PaymentsPage() {
  const t = useTranslations('payments');
  const [payments, setPayments] = useState<Payment[]>([]);
  const [summary, setSummary] = useState<PaymentSummary | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<PaymentFilter>('all');
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state for new payment
  const [formData, setFormData] = useState({
    customer_id: '',
    invoice_id: '',
    method: 'sinpe_movil' as Payment['method'],
    amount: '',
    sinpe_phone: '',
    sinpe_confirmation: '',
    reference_number: '',
    notes: '',
  });

  // Confirm/reject modal state
  const [confirmationCode, setConfirmationCode] = useState('');
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [paymentsData, summaryData, customersData, invoicesData, tenantData] = await Promise.all([
        api.getPayments({ limit: 100 }),
        api.getPaymentSummary(),
        api.getCustomers({ limit: 1000 }),
        api.getInvoices({ limit: 1000, status: 'sent' }),
        api.getCurrentTenant(),
      ]);
      setPayments(paymentsData.items);
      setSummary(summaryData);
      setCustomers(customersData.items);
      setInvoices(invoicesData.items);
      setTenant(tenantData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleRecordPayment() {
    setFormData({
      customer_id: '',
      invoice_id: '',
      method: 'sinpe_movil',
      amount: '',
      sinpe_phone: '',
      sinpe_confirmation: '',
      reference_number: '',
      notes: '',
    });
    setError(null);
    setShowRecordModal(true);
  }

  function handleViewDetail(payment: Payment) {
    setSelectedPayment(payment);
    setShowDetailModal(true);
  }

  function handleConfirmPayment(payment: Payment) {
    setSelectedPayment(payment);
    setConfirmationCode(payment.sinpe_confirmation || '');
    setShowConfirmModal(true);
  }

  function handleRejectPayment(payment: Payment) {
    setSelectedPayment(payment);
    setRejectReason('');
    setShowRejectModal(true);
  }

  async function submitPayment() {
    setSaving(true);
    setError(null);

    try {
      const isSinpe = formData.method === 'sinpe' || formData.method === 'sinpe_movil';

      if (isSinpe) {
        await api.recordSinpePayment({
          customer_id: formData.customer_id,
          invoice_id: formData.invoice_id || undefined,
          amount: parseFloat(formData.amount),
          sinpe_phone: formData.sinpe_phone || undefined,
          sinpe_confirmation: formData.sinpe_confirmation || undefined,
          notes: formData.notes || undefined,
        });
      } else {
        await api.recordPayment({
          customer_id: formData.customer_id,
          invoice_id: formData.invoice_id || undefined,
          method: formData.method,
          amount: parseFloat(formData.amount),
          reference_number: formData.reference_number || undefined,
          notes: formData.notes || undefined,
        } as Partial<Payment>);
      }

      setShowRecordModal(false);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al registrar el pago');
    } finally {
      setSaving(false);
    }
  }

  async function submitConfirmation() {
    if (!selectedPayment) return;
    setSaving(true);
    setError(null);

    try {
      await api.confirmPayment(selectedPayment.id, {
        sinpe_confirmation: confirmationCode || undefined,
      });
      setShowConfirmModal(false);
      setSelectedPayment(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al confirmar el pago');
    } finally {
      setSaving(false);
    }
  }

  async function submitRejection() {
    if (!selectedPayment) return;
    setSaving(true);
    setError(null);

    try {
      await api.rejectPayment(selectedPayment.id, rejectReason || undefined);
      setShowRejectModal(false);
      setSelectedPayment(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al rechazar el pago');
    } finally {
      setSaving(false);
    }
  }

  // Auto-fill amount when invoice selected
  function handleInvoiceSelect(invoiceId: string) {
    setFormData(prev => ({ ...prev, invoice_id: invoiceId }));
    if (invoiceId) {
      const invoice = invoices.find(i => i.id === invoiceId);
      if (invoice) {
        setFormData(prev => ({
          ...prev,
          amount: invoice.balance_due.toString(),
          customer_id: invoice.customer_id,
        }));
      }
    }
  }

  // Filter payments
  const filteredPayments = payments.filter(payment => {
    if (filter === 'all') return true;
    return payment.status === filter;
  });

  // Get pending payments count
  const pendingCount = payments.filter(p => p.status === 'pending').length;

  // Get customer name helper
  function getCustomerName(customerId: string): string {
    const customer = customers.find(c => c.id === customerId);
    return customer?.display_name || 'Cliente desconocido';
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
          <p className="text-gray-600">Registre y confirme pagos de clientes</p>
        </div>
        <Button onClick={handleRecordPayment}>
          <Plus className="w-4 h-4 mr-2" />
          {t('addPayment')}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Recibido</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(summary.confirmed_amount, 'CRC')}
                  </p>
                </div>
                <div className="p-3 bg-success-50 rounded-full">
                  <DollarSign className="w-6 h-6 text-success-600" />
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-2">{summary.confirmed_count} pagos confirmados</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pendientes</p>
                  <p className="text-2xl font-bold text-warning-600">
                    {formatCurrency(summary.pending_amount, 'CRC')}
                  </p>
                </div>
                <div className="p-3 bg-warning-50 rounded-full">
                  <Clock className="w-6 h-6 text-warning-600" />
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-2">{summary.pending_count} por confirmar</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">SINPE Movil</p>
                  <p className="text-2xl font-bold text-primary-600">
                    {formatCurrency(summary.by_method?.sinpe_movil?.amount || 0, 'CRC')}
                  </p>
                </div>
                <div className="p-3 bg-primary-50 rounded-full">
                  <Smartphone className="w-6 h-6 text-primary-600" />
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {summary.by_method?.sinpe_movil?.count || 0} pagos
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Otros Metodos</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(
                      (summary.by_method?.cash?.amount || 0) +
                      (summary.by_method?.bank_transfer?.amount || 0) +
                      (summary.by_method?.check?.amount || 0),
                      'CRC'
                    )}
                  </p>
                </div>
                <div className="p-3 bg-gray-100 rounded-full">
                  <CreditCard className="w-6 h-6 text-gray-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* SINPE Info Banner */}
      {tenant?.sinpe_number && (
        <Card className="border-primary-200 bg-primary-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white rounded-full">
                <Smartphone className="w-6 h-6 text-primary-600" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-primary-900">Su numero SINPE Movil</p>
                <p className="text-sm text-primary-700">
                  Comparta este numero con sus clientes para recibir pagos
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-mono font-bold text-primary-600">{tenant.sinpe_number}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pending Payments Alert */}
      {pendingCount > 0 && (
        <Alert variant="warning" title={`${pendingCount} pagos pendientes de confirmacion`}>
          Tiene pagos SINPE que requieren su confirmacion manual. Verifique en su cuenta bancaria
          y confirme los pagos recibidos.
        </Alert>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-2">
            <Button
              variant={filter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              Todos ({payments.length})
            </Button>
            <Button
              variant={filter === 'pending' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('pending')}
            >
              <Clock className="w-4 h-4 mr-1" />
              Pendientes ({payments.filter(p => p.status === 'pending').length})
            </Button>
            <Button
              variant={filter === 'confirmed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('confirmed')}
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Confirmados ({payments.filter(p => p.status === 'confirmed').length})
            </Button>
            <Button
              variant={filter === 'failed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('failed')}
            >
              <AlertTriangle className="w-4 h-4 mr-1" />
              Fallidos ({payments.filter(p => p.status === 'failed' || p.status === 'cancelled').length})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Payments List */}
      {filteredPayments.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <CreditCard className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {payments.length === 0
                ? 'No hay pagos registrados'
                : 'No hay pagos con este filtro'}
            </h3>
            <p className="text-gray-600 mb-4">
              {payments.length === 0
                ? 'Registre un pago cuando un cliente realice una transferencia SINPE.'
                : 'Pruebe con otro filtro para ver mas pagos.'}
            </p>
            {payments.length === 0 && (
              <Button onClick={handleRecordPayment}>
                <Plus className="w-4 h-4 mr-2" />
                Registrar Pago SINPE
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Pagos ({filteredPayments.length})</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-y border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Pago
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cliente
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metodo
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Monto
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredPayments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="font-medium text-gray-900">{payment.payment_number}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(payment.payment_date).toLocaleDateString('es-CR')}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-900">{getCustomerName(payment.customer_id)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {payment.method === 'sinpe_movil' ? (
                          <Smartphone className="w-4 h-4 text-primary-600" />
                        ) : payment.method === 'sinpe' ? (
                          <Smartphone className="w-4 h-4 text-blue-600" />
                        ) : (
                          <CreditCard className="w-4 h-4 text-gray-400" />
                        )}
                        <span className="text-sm">{paymentMethodLabels[payment.method]}</span>
                      </div>
                      {payment.sinpe_phone && (
                        <p className="text-xs text-gray-500 mt-1">Tel: {payment.sinpe_phone}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <p className="font-semibold text-gray-900">
                        {formatCurrency(payment.amount, payment.currency)}
                      </p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={getStatusBadgeVariant(payment.status)}>
                        {paymentStatusLabels[payment.status]}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleViewDetail(payment)}
                          className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                          title="Ver detalles"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {payment.status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleConfirmPayment(payment)}
                              className="p-2 text-gray-400 hover:text-success-600 hover:bg-success-50 rounded-lg"
                              title="Confirmar pago"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleRejectPayment(payment)}
                              className="p-2 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded-lg"
                              title="Rechazar pago"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Record Payment Modal */}
      <Modal
        isOpen={showRecordModal}
        onClose={() => setShowRecordModal(false)}
        title="Registrar Pago"
        size="lg"
      >
        <div className="space-y-6">
          {/* Payment Method */}
          <Select
            label="Metodo de Pago"
            value={formData.method}
            onChange={(e) => setFormData(prev => ({ ...prev, method: e.target.value as Payment['method'] }))}
            options={[
              { value: 'sinpe_movil', label: 'SINPE Movil' },
              { value: 'sinpe', label: 'Transferencia SINPE' },
              { value: 'bank_transfer', label: 'Transferencia Bancaria' },
              { value: 'cash', label: 'Efectivo' },
              { value: 'check', label: 'Cheque' },
              { value: 'other', label: 'Otro' },
            ]}
          />

          {/* Invoice Selection (optional) */}
          <Select
            label="Factura (opcional)"
            value={formData.invoice_id}
            onChange={(e) => handleInvoiceSelect(e.target.value)}
            options={[
              { value: '', label: 'Sin factura asociada' },
              ...invoices.map(inv => ({
                value: inv.id,
                label: `${inv.invoice_number} - ${getCustomerName(inv.customer_id)} - ${formatCurrency(inv.balance_due, 'CRC')}`,
              })),
            ]}
            placeholder="Seleccione una factura..."
          />

          {/* Customer Selection */}
          <Select
            label="Cliente"
            value={formData.customer_id}
            onChange={(e) => setFormData(prev => ({ ...prev, customer_id: e.target.value }))}
            options={customers.map(c => ({ value: c.id, label: c.display_name }))}
            placeholder="Seleccione un cliente..."
          />

          {/* Amount */}
          <Input
            label="Monto"
            type="number"
            min={0}
            step="0.01"
            value={formData.amount}
            onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
            placeholder="0.00"
          />

          {/* SINPE-specific fields */}
          {(formData.method === 'sinpe' || formData.method === 'sinpe_movil') && (
            <>
              <Input
                label="Telefono SINPE del Cliente"
                value={formData.sinpe_phone}
                onChange={(e) => setFormData(prev => ({ ...prev, sinpe_phone: e.target.value }))}
                placeholder="8888-8888"
                helperText="Numero desde el cual se realizo el pago"
              />
              <Input
                label="Codigo de Confirmacion SINPE"
                value={formData.sinpe_confirmation}
                onChange={(e) => setFormData(prev => ({ ...prev, sinpe_confirmation: e.target.value }))}
                placeholder="Ej: 123456"
                helperText="Codigo proporcionado por el cliente (opcional al registrar)"
              />
            </>
          )}

          {/* Reference Number (for non-SINPE) */}
          {formData.method !== 'sinpe' && formData.method !== 'sinpe_movil' && (
            <Input
              label="Numero de Referencia"
              value={formData.reference_number}
              onChange={(e) => setFormData(prev => ({ ...prev, reference_number: e.target.value }))}
              placeholder="Numero de cheque, transferencia, etc."
            />
          )}

          {/* Notes */}
          <Textarea
            label="Notas (opcional)"
            value={formData.notes}
            onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
            placeholder="Informacion adicional..."
          />

          {/* Info about SINPE workflow */}
          {(formData.method === 'sinpe' || formData.method === 'sinpe_movil') && (
            <Alert variant="info" title="Proceso de Confirmacion">
              El pago quedara como pendiente hasta que lo confirme manualmente.
              Verifique el deposito en su cuenta bancaria antes de confirmar.
            </Alert>
          )}
        </div>

        <ModalFooter>
          <Button variant="outline" onClick={() => setShowRecordModal(false)}>
            Cancelar
          </Button>
          <Button
            onClick={submitPayment}
            isLoading={saving}
            disabled={!formData.customer_id || !formData.amount}
          >
            Registrar Pago
          </Button>
        </ModalFooter>
      </Modal>

      {/* View Payment Detail Modal */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="Detalle del Pago"
        size="md"
      >
        {selectedPayment && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Numero de Pago</p>
                <p className="font-medium">{selectedPayment.payment_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Estado</p>
                <Badge variant={getStatusBadgeVariant(selectedPayment.status)}>
                  {paymentStatusLabels[selectedPayment.status]}
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Cliente</p>
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-gray-400" />
                  <span className="font-medium">{getCustomerName(selectedPayment.customer_id)}</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Fecha</p>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span>{new Date(selectedPayment.payment_date).toLocaleDateString('es-CR')}</span>
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Metodo</p>
                  <div className="flex items-center gap-2">
                    {selectedPayment.method === 'sinpe_movil' ? (
                      <Smartphone className="w-4 h-4 text-primary-600" />
                    ) : (
                      <CreditCard className="w-4 h-4 text-gray-400" />
                    )}
                    <span>{paymentMethodLabels[selectedPayment.method]}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Monto</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatCurrency(selectedPayment.amount, selectedPayment.currency)}
                  </p>
                </div>
              </div>
            </div>

            {(selectedPayment.sinpe_phone || selectedPayment.sinpe_confirmation) && (
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Informacion SINPE</h4>
                <div className="grid grid-cols-2 gap-4">
                  {selectedPayment.sinpe_phone && (
                    <div>
                      <p className="text-sm text-gray-500">Telefono</p>
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-gray-400" />
                        <span>{selectedPayment.sinpe_phone}</span>
                      </div>
                    </div>
                  )}
                  {selectedPayment.sinpe_confirmation && (
                    <div>
                      <p className="text-sm text-gray-500">Codigo Confirmacion</p>
                      <div className="flex items-center gap-2">
                        <Hash className="w-4 h-4 text-gray-400" />
                        <span className="font-mono">{selectedPayment.sinpe_confirmation}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedPayment.invoice_id && (
              <div className="border-t pt-4">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-500">Factura asociada</span>
                </div>
              </div>
            )}

            {selectedPayment.confirmed_at && (
              <div className="border-t pt-4">
                <p className="text-sm text-gray-500">Confirmado el</p>
                <p>{new Date(selectedPayment.confirmed_at).toLocaleString('es-CR')}</p>
              </div>
            )}

            {selectedPayment.notes && (
              <div className="border-t pt-4">
                <p className="text-sm text-gray-500">Notas</p>
                <p className="text-gray-700">{selectedPayment.notes}</p>
              </div>
            )}
          </div>
        )}

        <ModalFooter>
          <Button variant="outline" onClick={() => setShowDetailModal(false)}>
            Cerrar
          </Button>
          {selectedPayment?.status === 'pending' && (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  setShowDetailModal(false);
                  handleRejectPayment(selectedPayment);
                }}
              >
                <X className="w-4 h-4 mr-2" />
                Rechazar
              </Button>
              <Button
                onClick={() => {
                  setShowDetailModal(false);
                  handleConfirmPayment(selectedPayment);
                }}
              >
                <Check className="w-4 h-4 mr-2" />
                Confirmar
              </Button>
            </>
          )}
        </ModalFooter>
      </Modal>

      {/* Confirm Payment Modal */}
      <Modal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        title="Confirmar Pago"
        size="sm"
      >
        <div className="space-y-4">
          <Alert variant="info" title="Verificacion">
            Antes de confirmar, asegurese de que el deposito aparece en su cuenta bancaria.
          </Alert>

          {selectedPayment && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Monto:</span>
                <span className="font-bold text-lg">
                  {formatCurrency(selectedPayment.amount, selectedPayment.currency)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cliente:</span>
                <span>{getCustomerName(selectedPayment.customer_id)}</span>
              </div>
            </div>
          )}

          <Input
            label="Codigo de Confirmacion SINPE"
            value={confirmationCode}
            onChange={(e) => setConfirmationCode(e.target.value)}
            placeholder="Codigo proporcionado por el banco"
            helperText="Opcional: Agregue el codigo de confirmacion de su banco"
          />
        </div>

        <ModalFooter>
          <Button variant="outline" onClick={() => setShowConfirmModal(false)}>
            Cancelar
          </Button>
          <Button onClick={submitConfirmation} isLoading={saving}>
            <CheckCircle className="w-4 h-4 mr-2" />
            Confirmar Pago
          </Button>
        </ModalFooter>
      </Modal>

      {/* Reject Payment Modal */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Rechazar Pago"
        size="sm"
      >
        <div className="space-y-4">
          <Alert variant="warning" title="Atencion">
            Al rechazar este pago, se marcara como fallido y no se aplicara a ninguna factura.
          </Alert>

          {selectedPayment && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Monto:</span>
                <span className="font-bold text-lg">
                  {formatCurrency(selectedPayment.amount, selectedPayment.currency)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cliente:</span>
                <span>{getCustomerName(selectedPayment.customer_id)}</span>
              </div>
            </div>
          )}

          <Textarea
            label="Razon del Rechazo"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Ej: No se encontro el deposito en la cuenta bancaria"
          />
        </div>

        <ModalFooter>
          <Button variant="outline" onClick={() => setShowRejectModal(false)}>
            Cancelar
          </Button>
          <Button variant="danger" onClick={submitRejection} isLoading={saving}>
            <X className="w-4 h-4 mr-2" />
            Rechazar Pago
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
