'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Alert } from '@/components/ui/alert';
import { DataTable, Column } from '@/components/ui/data-table';
import { CustomerForm } from '@/components/forms/CustomerForm';
import type { Customer } from '@/types';
import { Plus, Search, Users, Edit, Trash2, Phone, Mail, Building, User } from 'lucide-react';

export default function CustomersPage() {
  const t = useTranslations('customers');
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Customer | null>(null);

  useEffect(() => {
    loadCustomers();
  }, []);

  async function loadCustomers() {
    try {
      const data = await api.getCustomers({ search: search || undefined, limit: 1000 });
      setCustomers(data.items);
    } catch (error) {
      console.error('Failed to load customers:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch() {
    setLoading(true);
    await loadCustomers();
  }

  function handleAdd() {
    setEditingCustomer(null);
    setError(null);
    setShowModal(true);
  }

  function handleEdit(customer: Customer) {
    setEditingCustomer(customer);
    setError(null);
    setShowModal(true);
  }

  async function handleSubmit(data: any) {
    setSaving(true);
    setError(null);

    try {
      if (editingCustomer) {
        await api.updateCustomer(editingCustomer.id, data);
      } else {
        await api.createCustomer(data);
      }
      setShowModal(false);
      setEditingCustomer(null);
      await loadCustomers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar el cliente');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(customer: Customer) {
    try {
      await api.deleteCustomer(customer.id);
      setDeleteConfirm(null);
      await loadCustomers();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al eliminar el cliente');
      setDeleteConfirm(null);
    }
  }

  // Filter customers by search term
  const filteredCustomers = customers.filter(customer =>
    customer.display_name.toLowerCase().includes(search.toLowerCase()) ||
    customer.email.toLowerCase().includes(search.toLowerCase()) ||
    customer.phone.includes(search)
  );

  // Define table columns
  const columns: Column<Customer>[] = [
    {
      key: 'display_name',
      header: 'Cliente',
      sortable: true,
      render: (customer) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-50 rounded-full flex items-center justify-center">
            {customer.customer_type === 'business' ? (
              <Building className="w-5 h-5 text-primary-600" />
            ) : (
              <User className="w-5 h-5 text-primary-600" />
            )}
          </div>
          <div>
            <p className="font-medium text-gray-900">{customer.display_name}</p>
            {customer.cedula && (
              <p className="text-sm text-gray-500">Cedula: {customer.cedula}</p>
            )}
            {customer.cedula_juridica && (
              <p className="text-sm text-gray-500">Cedula Jur.: {customer.cedula_juridica}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'email',
      header: 'Contacto',
      sortable: true,
      render: (customer) => (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Mail className="w-4 h-4" />
            {customer.email}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Phone className="w-4 h-4" />
            {customer.phone}
          </div>
        </div>
      ),
    },
    {
      key: 'customer_type',
      header: 'Tipo',
      sortable: true,
      render: (customer) => (
        <Badge variant={customer.customer_type === 'business' ? 'info' : 'default'}>
          {customer.customer_type === 'business' ? 'Empresa' : 'Individual'}
        </Badge>
      ),
    },
    {
      key: 'province',
      header: 'Ubicacion',
      sortable: true,
      render: (customer) => (
        <span className="text-sm text-gray-600">
          {customer.city && customer.province
            ? `${customer.city}, ${customer.province}`
            : customer.province || customer.city || '-'}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Estado',
      sortable: true,
      render: (customer) => (
        <Badge variant={customer.is_active ? 'success' : 'default'}>
          {customer.is_active ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Acciones',
      headerClassName: 'text-right',
      className: 'text-right',
      render: (customer) => (
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(customer);
            }}
            className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setDeleteConfirm(customer);
            }}
            className="p-2 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded-lg"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
          <p className="text-gray-600">{customers.length} clientes registrados</p>
        </div>
        <Button onClick={handleAdd}>
          <Plus className="w-4 h-4 mr-2" />
          {t('addCustomer')}
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Buscar por nombre, correo o telefono..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
              />
            </div>
            <Button variant="outline" onClick={handleSearch}>
              Buscar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Customers List */}
      {filteredCustomers.length === 0 && !loading ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {customers.length === 0 ? 'No hay clientes registrados' : 'No se encontraron resultados'}
            </h3>
            <p className="text-gray-600 mb-4">
              {customers.length === 0
                ? 'Comience agregando su primer cliente para crear contratos y facturas.'
                : 'Intente con otros terminos de busqueda.'}
            </p>
            {customers.length === 0 && (
              <Button onClick={handleAdd}>
                <Plus className="w-4 h-4 mr-2" />
                Agregar Primer Cliente
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Clientes ({filteredCustomers.length})</CardTitle>
          </CardHeader>
          <DataTable
            data={filteredCustomers}
            columns={columns}
            keyExtractor={(customer) => customer.id}
            pageSize={10}
            showPagination={true}
            loading={loading}
            emptyMessage="No hay clientes para mostrar"
            onRowClick={handleEdit}
          />
        </Card>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={editingCustomer ? t('editCustomer') : t('addCustomer')}
        size="lg"
      >
        <CustomerForm
          customer={editingCustomer}
          onSubmit={handleSubmit}
          onCancel={() => setShowModal(false)}
          isLoading={saving}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        title="Confirmar Eliminacion"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            ¿Esta seguro que desea eliminar al cliente <strong>{deleteConfirm?.display_name}</strong>?
            Esta accion no se puede deshacer.
          </p>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
              Cancelar
            </Button>
            <Button variant="danger" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>
              Eliminar
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
