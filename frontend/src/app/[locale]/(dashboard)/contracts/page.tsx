'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge, getStatusBadgeVariant } from '@/components/ui/badge';
import { Modal, ModalFooter } from '@/components/ui/modal';
import { Alert } from '@/components/ui/alert';
import { ContractForm } from '@/components/forms/ContractForm';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Contract, Customer, StorageUnit } from '@/types';
import {
  Plus, Search, FileText, Edit, Trash2, LogIn, LogOut,
  Calendar, DollarSign, Package, User
} from 'lucide-react';

export default function ContractsPage() {
  const t = useTranslations('contracts');
  const { tenant } = useAuthStore();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [customers, setCustomers] = useState<Record<string, Customer>>({});
  const [units, setUnits] = useState<Record<string, StorageUnit>>({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showModal, setShowModal] = useState(false);
  const [editingContract, setEditingContract] = useState<Contract | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Contract | null>(null);
  const [moveInContract, setMoveInContract] = useState<Contract | null>(null);
  const [moveOutContract, setMoveOutContract] = useState<Contract | null>(null);
  const [moveInData, setMoveInData] = useState({ move_in_date: '', deposit_paid: false, access_code: '' });
  const [moveOutData, setMoveOutData] = useState({ move_out_date: '', return_deposit: false, notes: '' });

  const currency = tenant?.currency || 'CRC';

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function loadData() {
    try {
      const [contractsData, customersData, unitsData] = await Promise.all([
        api.getContracts({ status: statusFilter || undefined }),
        api.getCustomers({ limit: 1000 }),
        api.getStorageUnits({ limit: 1000 }),
      ]);

      setContracts(contractsData.items);

      // Create lookup maps
      const customersMap: Record<string, Customer> = {};
      customersData.items.forEach(c => { customersMap[c.id] = c; });
      setCustomers(customersMap);

      const unitsMap: Record<string, StorageUnit> = {};
      unitsData.items.forEach(u => { unitsMap[u.id] = u; });
      setUnits(unitsMap);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleAdd() {
    setEditingContract(null);
    setError(null);
    setShowModal(true);
  }

  function handleEdit(contract: Contract) {
    setEditingContract(contract);
    setError(null);
    setShowModal(true);
  }

  async function handleSubmit(data: any) {
    setSaving(true);
    setError(null);

    try {
      if (editingContract) {
        await api.updateContract(editingContract.id, data);
      } else {
        await api.createContract(data);
      }
      setShowModal(false);
      setEditingContract(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar el contrato');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(contract: Contract) {
    try {
      await api.updateContract(contract.id, { status: 'terminated' });
      setDeleteConfirm(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al eliminar el contrato');
      setDeleteConfirm(null);
    }
  }

  function openMoveIn(contract: Contract) {
    setMoveInData({
      move_in_date: new Date().toISOString().split('T')[0],
      deposit_paid: false,
      access_code: contract.access_code || '',
    });
    setMoveInContract(contract);
  }

  async function handleMoveIn() {
    if (!moveInContract) return;
    setSaving(true);
    setError(null);

    try {
      await api.processMoveIn(moveInContract.id, moveInData);
      setMoveInContract(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar entrada');
    } finally {
      setSaving(false);
    }
  }

  function openMoveOut(contract: Contract) {
    setMoveOutData({
      move_out_date: new Date().toISOString().split('T')[0],
      return_deposit: false,
      notes: '',
    });
    setMoveOutContract(contract);
  }

  async function handleMoveOut() {
    if (!moveOutContract) return;
    setSaving(true);
    setError(null);

    try {
      await api.processMoveOut(moveOutContract.id, moveOutData);
      setMoveOutContract(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar salida');
    } finally {
      setSaving(false);
    }
  }

  const statsCounts = {
    total: contracts.length,
    draft: contracts.filter(c => c.status === 'draft').length,
    active: contracts.filter(c => c.status === 'active').length,
    terminated: contracts.filter(c => c.status === 'terminated' || c.status === 'expired').length,
  };

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
          <p className="text-gray-600">{contracts.length} contratos</p>
        </div>
        <Button onClick={handleAdd}>
          <Plus className="w-4 h-4 mr-2" />
          {t('addContract')}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:border-primary-300" onClick={() => setStatusFilter('')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{statsCounts.total}</p>
            <p className="text-sm text-gray-600">Total</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-gray-300" onClick={() => setStatusFilter('draft')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-600">{statsCounts.draft}</p>
            <p className="text-sm text-gray-600">{t('statuses.draft')}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-success-300" onClick={() => setStatusFilter('active')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-success-600">{statsCounts.active}</p>
            <p className="text-sm text-gray-600">{t('statuses.active')}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-danger-300" onClick={() => setStatusFilter('terminated')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-danger-600">{statsCounts.terminated}</p>
            <p className="text-sm text-gray-600">Finalizados</p>
          </CardContent>
        </Card>
      </div>

      {/* Contracts List */}
      {contracts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No hay contratos
            </h3>
            <p className="text-gray-600 mb-4">
              Cree un nuevo contrato para asignar una unidad a un cliente.
            </p>
            <Button onClick={handleAdd}>
              <Plus className="w-4 h-4 mr-2" />
              Crear Primer Contrato
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                {statusFilter ? t(`statuses.${statusFilter}`) : 'Todos los Contratos'}
              </CardTitle>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">Todos</option>
                <option value="draft">{t('statuses.draft')}</option>
                <option value="active">{t('statuses.active')}</option>
                <option value="terminated">{t('statuses.terminated')}</option>
              </select>
            </div>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-y border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Contrato</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unidad</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Periodo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tarifa</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {contracts.map((contract) => {
                  const customer = customers[contract.customer_id];
                  const unit = units[contract.unit_id];

                  return (
                    <tr key={contract.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
                            <FileText className="w-5 h-5 text-primary-600" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{contract.contract_number}</p>
                            <p className="text-sm text-gray-500">
                              {contract.is_month_to_month ? 'Mes a mes' : 'Plazo fijo'}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-900">
                            {customer?.display_name || 'Cliente no encontrado'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <Package className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-900">
                            {unit?.unit_number || 'Unidad no encontrada'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          <div className="flex items-center gap-1 text-gray-900">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            {formatDate(contract.start_date)}
                          </div>
                          {contract.end_date && (
                            <p className="text-gray-500">
                              hasta {formatDate(contract.end_date)}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          <div className="flex items-center gap-1 font-medium text-gray-900">
                            <DollarSign className="w-4 h-4 text-gray-400" />
                            {formatCurrency(contract.effective_monthly_rate, currency)}
                          </div>
                          {contract.discount_percent && contract.discount_percent > 0 && (
                            <p className="text-success-600 text-xs">
                              {contract.discount_percent}% descuento
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={getStatusBadgeVariant(contract.status)}>
                          {t(`statuses.${contract.status}`)}
                        </Badge>
                        {contract.deposit_paid && (
                          <p className="text-xs text-success-600 mt-1">Deposito pagado</p>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-1">
                          {contract.status === 'draft' && (
                            <>
                              <button
                                onClick={() => openMoveIn(contract)}
                                className="p-2 text-success-600 hover:bg-success-50 rounded-lg"
                                title="Registrar Entrada"
                              >
                                <LogIn className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleEdit(contract)}
                                className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(contract)}
                                className="p-2 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded-lg"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          {contract.status === 'active' && (
                            <button
                              onClick={() => openMoveOut(contract)}
                              className="p-2 text-danger-600 hover:bg-danger-50 rounded-lg"
                              title="Registrar Salida"
                            >
                              <LogOut className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingContract ? t('editContract') : t('addContract')}
        size="xl"
      >
        <ContractForm
          contract={editingContract}
          onSubmit={handleSubmit}
          onCancel={() => setShowModal(false)}
          isLoading={saving}
        />
      </Modal>

      {/* Move In Modal */}
      <Modal
        isOpen={!!moveInContract}
        onClose={() => setMoveInContract(null)}
        title={t('moveIn')}
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Registrar entrada para el contrato <strong>{moveInContract?.contract_number}</strong>
          </p>

          <Input
            label="Fecha de Entrada"
            type="date"
            value={moveInData.move_in_date}
            onChange={(e) => setMoveInData({ ...moveInData, move_in_date: e.target.value })}
          />

          <Input
            label="Codigo de Acceso"
            value={moveInData.access_code}
            onChange={(e) => setMoveInData({ ...moveInData, access_code: e.target.value })}
            placeholder="Ej: 1234"
          />

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={moveInData.deposit_paid}
              onChange={(e) => setMoveInData({ ...moveInData, deposit_paid: e.target.checked })}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              Deposito pagado ({formatCurrency(moveInContract?.deposit_amount || 0, currency)})
            </span>
          </label>

          <ModalFooter>
            <Button variant="outline" onClick={() => setMoveInContract(null)}>
              Cancelar
            </Button>
            <Button onClick={handleMoveIn} isLoading={saving}>
              <LogIn className="w-4 h-4 mr-2" />
              Confirmar Entrada
            </Button>
          </ModalFooter>
        </div>
      </Modal>

      {/* Move Out Modal */}
      <Modal
        isOpen={!!moveOutContract}
        onClose={() => setMoveOutContract(null)}
        title={t('moveOut')}
        size="md"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Registrar salida para el contrato <strong>{moveOutContract?.contract_number}</strong>
          </p>

          <Input
            label="Fecha de Salida"
            type="date"
            value={moveOutData.move_out_date}
            onChange={(e) => setMoveOutData({ ...moveOutData, move_out_date: e.target.value })}
          />

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={moveOutData.return_deposit}
              onChange={(e) => setMoveOutData({ ...moveOutData, return_deposit: e.target.checked })}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              Devolver deposito ({formatCurrency(moveOutContract?.deposit_amount || 0, currency)})
            </span>
          </label>

          <Input
            label="Notas (opcional)"
            value={moveOutData.notes}
            onChange={(e) => setMoveOutData({ ...moveOutData, notes: e.target.value })}
            placeholder="Observaciones sobre el estado de la unidad..."
          />

          <ModalFooter>
            <Button variant="outline" onClick={() => setMoveOutContract(null)}>
              Cancelar
            </Button>
            <Button variant="danger" onClick={handleMoveOut} isLoading={saving}>
              <LogOut className="w-4 h-4 mr-2" />
              Confirmar Salida
            </Button>
          </ModalFooter>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        title="Cancelar Contrato"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            ¿Esta seguro que desea cancelar el contrato <strong>{deleteConfirm?.contract_number}</strong>?
          </p>
          <ModalFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
              Volver
            </Button>
            <Button variant="danger" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>
              Cancelar Contrato
            </Button>
          </ModalFooter>
        </div>
      </Modal>
    </div>
  );
}
