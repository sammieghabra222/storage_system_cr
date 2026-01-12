'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge, getStatusBadgeVariant } from '@/components/ui/badge';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Alert } from '@/components/ui/alert';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Invoice, InvoiceSummary, Customer, Contract } from '@/types';
import {
  Plus, Receipt, Send, XCircle, Eye, Calendar, DollarSign,
  AlertCircle, CheckCircle
} from 'lucide-react';

export default function InvoicesPage() {
  const t = useTranslations('invoices');
  const { tenant } = useAuthStore();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [summary, setSummary] = useState<InvoiceSummary | null>(null);
  const [customers, setCustomers] = useState<Record<string, Customer>>({});
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [viewingInvoice, setViewingInvoice] = useState<Invoice | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create form state
  const [createForm, setCreateForm] = useState({
    customer_id: '',
    contract_id: '',
    due_date: '',
    description: '',
    amount: '',
    tax_rate: '13',
  });

  const currency = tenant?.currency || 'CRC';

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function loadData() {
    try {
      const [invoicesData, summaryData, customersData, contractsData] = await Promise.all([
        api.getInvoices({ status: statusFilter || undefined }),
        api.getInvoiceSummary(),
        api.getCustomers({ limit: 1000 }),
        api.getContracts({ status: 'active' }),
      ]);

      setInvoices(invoicesData.items);
      setSummary(summaryData);
      setContracts(contractsData.items);

      const customersMap: Record<string, Customer> = {};
      customersData.items.forEach(c => { customersMap[c.id] = c; });
      setCustomers(customersMap);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + 30);

    setCreateForm({
      customer_id: '',
      contract_id: '',
      due_date: dueDate.toISOString().split('T')[0],
      description: 'Alquiler de unidad de almacenamiento',
      amount: '',
      tax_rate: '13',
    });
    setError(null);
    setShowCreateModal(true);
  }

  async function handleCreate() {
    if (!createForm.customer_id || !createForm.amount || !createForm.due_date) {
      setError('Complete todos los campos requeridos');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const amount = parseFloat(createForm.amount);
      const taxRate = parseFloat(createForm.tax_rate);

      await api.createInvoice({
        customer_id: createForm.customer_id,
        contract_id: createForm.contract_id || undefined,
        due_date: createForm.due_date,
        line_items: [{
          description: createForm.description,
          quantity: 1,
          unit_price: amount,
          tax_rate: taxRate,
          discount_percent: 0,
        }],
      });

      setShowCreateModal(false);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear la factura');
    } finally {
      setSaving(false);
    }
  }

  async function handleSend(invoice: Invoice) {
    try {
      await api.sendInvoice(invoice.id);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al enviar la factura');
    }
  }

  async function handleCancel(invoice: Invoice) {
    try {
      await api.cancelInvoice(invoice.id);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cancelar la factura');
    }
  }

  // When contract is selected, auto-fill customer and amount
  function handleContractChange(contractId: string) {
    const contract = contracts.find(c => c.id === contractId);
    if (contract) {
      setCreateForm({
        ...createForm,
        contract_id: contractId,
        customer_id: contract.customer_id,
        amount: contract.effective_monthly_rate.toString(),
      });
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
          <p className="text-gray-600">{invoices.length} facturas</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4 mr-2" />
          {t('addInvoice')}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-50 rounded-lg">
                <DollarSign className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Facturado</p>
                <p className="text-lg font-bold text-gray-900">
                  {formatCurrency(summary?.total_amount || 0, currency)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-success-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-success-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pagado</p>
                <p className="text-lg font-bold text-success-600">
                  {formatCurrency(summary?.total_paid || 0, currency)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-warning-50 rounded-lg">
                <Calendar className="w-5 h-5 text-warning-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Pendiente</p>
                <p className="text-lg font-bold text-warning-600">
                  {formatCurrency(summary?.total_outstanding || 0, currency)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-danger-300" onClick={() => setStatusFilter('overdue')}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-danger-50 rounded-lg">
                <AlertCircle className="w-5 h-5 text-danger-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Vencidas ({summary?.overdue_count || 0})</p>
                <p className="text-lg font-bold text-danger-600">
                  {formatCurrency(summary?.overdue_amount || 0, currency)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invoices List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Facturas</CardTitle>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">Todas</option>
              <option value="draft">{t('statuses.draft')}</option>
              <option value="sent">{t('statuses.sent')}</option>
              <option value="paid">{t('statuses.paid')}</option>
              <option value="overdue">{t('statuses.overdue')}</option>
              <option value="cancelled">{t('statuses.cancelled')}</option>
            </select>
          </div>
        </CardHeader>
        {invoices.length === 0 ? (
          <CardContent className="py-12 text-center">
            <Receipt className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No hay facturas</h3>
            <p className="text-gray-600 mb-4">Cree una factura para un cliente o contrato activo.</p>
            <Button onClick={openCreate}>
              <Plus className="w-4 h-4 mr-2" />
              Crear Primera Factura
            </Button>
          </CardContent>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-y border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Factura</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fechas</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Saldo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoices.map((invoice) => {
                  const customer = customers[invoice.customer_id];

                  return (
                    <tr key={invoice.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
                            <Receipt className="w-5 h-5 text-primary-600" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{invoice.invoice_number}</p>
                            <p className="text-sm text-gray-500">{invoice.currency}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">
                          {customer?.display_name || 'Cliente no encontrado'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          <p className="text-gray-900">Emision: {formatDate(invoice.issue_date)}</p>
                          <p className={invoice.is_overdue ? 'text-danger-600 font-medium' : 'text-gray-500'}>
                            Vence: {formatDate(invoice.due_date)}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-gray-900">
                          {formatCurrency(invoice.total, currency)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`font-medium ${invoice.balance_due > 0 ? 'text-danger-600' : 'text-success-600'}`}>
                          {formatCurrency(invoice.balance_due, currency)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={getStatusBadgeVariant(invoice.status)}>
                          {t(`statuses.${invoice.status}`)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => setViewingInvoice(invoice)}
                            className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                            title="Ver detalle"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {invoice.status === 'draft' && (
                            <>
                              <button
                                onClick={() => handleSend(invoice)}
                                className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg"
                                title="Enviar"
                              >
                                <Send className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleCancel(invoice)}
                                className="p-2 text-danger-600 hover:bg-danger-50 rounded-lg"
                                title="Cancelar"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create Invoice Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Nueva Factura"
        size="md"
      >
        <div className="space-y-4">
          <Select
            label="Contrato Activo (opcional)"
            options={contracts.map(c => ({
              value: c.id,
              label: `${c.contract_number} - ${customers[c.customer_id]?.display_name || 'Cliente'}`,
            }))}
            placeholder="Seleccione un contrato..."
            value={createForm.contract_id}
            onChange={(e) => handleContractChange(e.target.value)}
          />

          <Select
            label="Cliente"
            options={Object.values(customers).map(c => ({
              value: c.id,
              label: c.display_name,
            }))}
            placeholder="Seleccione un cliente..."
            value={createForm.customer_id}
            onChange={(e) => setCreateForm({ ...createForm, customer_id: e.target.value })}
          />

          <Input
            label="Fecha de Vencimiento"
            type="date"
            value={createForm.due_date}
            onChange={(e) => setCreateForm({ ...createForm, due_date: e.target.value })}
          />

          <Input
            label="Descripcion"
            value={createForm.description}
            onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Monto (antes de IVA)"
              type="number"
              min={0}
              step="0.01"
              value={createForm.amount}
              onChange={(e) => setCreateForm({ ...createForm, amount: e.target.value })}
            />
            <Input
              label="IVA %"
              type="number"
              min={0}
              max={100}
              value={createForm.tax_rate}
              onChange={(e) => setCreateForm({ ...createForm, tax_rate: e.target.value })}
            />
          </div>

          {createForm.amount && (
            <div className="p-3 bg-gray-50 rounded-lg text-sm">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>{formatCurrency(parseFloat(createForm.amount) || 0, currency)}</span>
              </div>
              <div className="flex justify-between">
                <span>IVA ({createForm.tax_rate}%):</span>
                <span>
                  {formatCurrency((parseFloat(createForm.amount) || 0) * (parseFloat(createForm.tax_rate) / 100), currency)}
                </span>
              </div>
              <div className="flex justify-between font-bold border-t pt-2 mt-2">
                <span>Total:</span>
                <span>
                  {formatCurrency((parseFloat(createForm.amount) || 0) * (1 + parseFloat(createForm.tax_rate) / 100), currency)}
                </span>
              </div>
            </div>
          )}

          <ModalFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancelar
            </Button>
            <Button onClick={handleCreate} isLoading={saving}>
              Crear Factura
            </Button>
          </ModalFooter>
        </div>
      </Modal>

      {/* View Invoice Modal */}
      <Modal
        isOpen={!!viewingInvoice}
        onClose={() => setViewingInvoice(null)}
        title={`Factura ${viewingInvoice?.invoice_number}`}
        size="lg"
      >
        {viewingInvoice && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Cliente</p>
                <p className="font-medium">{customers[viewingInvoice.customer_id]?.display_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Estado</p>
                <Badge variant={getStatusBadgeVariant(viewingInvoice.status)}>
                  {t(`statuses.${viewingInvoice.status}`)}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-gray-500">Fecha de Emision</p>
                <p className="font-medium">{formatDate(viewingInvoice.issue_date)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Fecha de Vencimiento</p>
                <p className={`font-medium ${viewingInvoice.is_overdue ? 'text-danger-600' : ''}`}>
                  {formatDate(viewingInvoice.due_date)}
                </p>
              </div>
            </div>

            <div className="border-t pt-4">
              <h4 className="font-medium mb-3">Detalle</h4>
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">Descripcion</th>
                    <th className="px-3 py-2 text-right">Cant.</th>
                    <th className="px-3 py-2 text-right">Precio</th>
                    <th className="px-3 py-2 text-right">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {viewingInvoice.line_items.map((item, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-3 py-2">{item.description}</td>
                      <td className="px-3 py-2 text-right">{item.quantity}</td>
                      <td className="px-3 py-2 text-right">{formatCurrency(item.unit_price, currency)}</td>
                      <td className="px-3 py-2 text-right">{formatCurrency(item.total, currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>{formatCurrency(viewingInvoice.subtotal, currency)}</span>
              </div>
              <div className="flex justify-between">
                <span>IVA:</span>
                <span>{formatCurrency(viewingInvoice.tax_total, currency)}</span>
              </div>
              <div className="flex justify-between font-bold text-lg">
                <span>Total:</span>
                <span>{formatCurrency(viewingInvoice.total, currency)}</span>
              </div>
              <div className="flex justify-between text-success-600">
                <span>Pagado:</span>
                <span>{formatCurrency(viewingInvoice.amount_paid, currency)}</span>
              </div>
              <div className="flex justify-between font-bold text-danger-600">
                <span>Saldo:</span>
                <span>{formatCurrency(viewingInvoice.balance_due, currency)}</span>
              </div>
            </div>

            <ModalFooter>
              <Button variant="outline" onClick={() => setViewingInvoice(null)}>
                Cerrar
              </Button>
            </ModalFooter>
          </div>
        )}
      </Modal>
    </div>
  );
}
