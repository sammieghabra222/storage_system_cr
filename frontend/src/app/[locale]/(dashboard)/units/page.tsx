'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useAuthStore } from '@/stores/auth';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge, getStatusBadgeVariant } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';
import type { StorageUnit, StorageUnitStats } from '@/types';
import { Plus, Search, Package, Edit, Trash2 } from 'lucide-react';

export default function UnitsPage() {
  const t = useTranslations('units');
  const { tenant } = useAuthStore();
  const [units, setUnits] = useState<StorageUnit[]>([]);
  const [stats, setStats] = useState<StorageUnitStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function loadData() {
    try {
      const [unitsData, statsData] = await Promise.all([
        api.getStorageUnits({ status: statusFilter || undefined }),
        api.getStorageUnitStats(),
      ]);
      setUnits(unitsData.items);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load units:', error);
    } finally {
      setLoading(false);
    }
  }

  const filteredUnits = units.filter(unit =>
    unit.unit_number.toLowerCase().includes(search.toLowerCase()) ||
    (unit.building && unit.building.toLowerCase().includes(search.toLowerCase()))
  );

  const currency = tenant?.currency || 'CRC';

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
            {stats?.total} unidades totales - {stats?.occupancy_rate}% ocupacion
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          {t('addUnit')}
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="cursor-pointer hover:border-primary-300" onClick={() => setStatusFilter('')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{stats?.total || 0}</p>
            <p className="text-sm text-gray-600">Total</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-success-300" onClick={() => setStatusFilter('available')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-success-600">{stats?.available || 0}</p>
            <p className="text-sm text-gray-600">{t('statuses.available')}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-primary-300" onClick={() => setStatusFilter('occupied')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-primary-600">{stats?.occupied || 0}</p>
            <p className="text-sm text-gray-600">{t('statuses.occupied')}</p>
          </CardContent>
        </Card>
        <Card className="cursor-pointer hover:border-warning-300" onClick={() => setStatusFilter('reserved')}>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-warning-600">{stats?.reserved || 0}</p>
            <p className="text-sm text-gray-600">{t('statuses.reserved')}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Buscar por numero o edificio..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Todos los estados</option>
              <option value="available">{t('statuses.available')}</option>
              <option value="occupied">{t('statuses.occupied')}</option>
              <option value="reserved">{t('statuses.reserved')}</option>
              <option value="maintenance">{t('statuses.maintenance')}</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Units Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {statusFilter ? t(`statuses.${statusFilter}`) : 'Todas las Unidades'} ({filteredUnits.length})
          </CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-y border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('unitNumber')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('unitType')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('status')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('size')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('monthlyRate')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('features')}
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredUnits.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    <Package className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No se encontraron unidades</p>
                  </td>
                </tr>
              ) : (
                filteredUnits.map((unit) => (
                  <tr key={unit.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
                          <Package className="w-5 h-5 text-primary-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{unit.unit_number}</p>
                          {unit.building && (
                            <p className="text-sm text-gray-500">{unit.building}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600">
                        {t(`types.${unit.unit_type}`)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge variant={getStatusBadgeVariant(unit.status)}>
                        {t(`statuses.${unit.status}`)}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600">
                        {unit.area_sqm ? `${unit.area_sqm} m²` : '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium text-gray-900">
                        {formatCurrency(unit.monthly_rate, currency)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {unit.has_climate_control && (
                          <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded">AC</span>
                        )}
                        {unit.has_electricity && (
                          <span className="text-xs px-2 py-0.5 bg-yellow-50 text-yellow-600 rounded">Luz</span>
                        )}
                        {unit.is_drive_up && (
                          <span className="text-xs px-2 py-0.5 bg-green-50 text-green-600 rounded">Acceso</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded-lg">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
