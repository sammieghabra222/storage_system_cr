'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { api } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { ModalFooter } from '@/components/ui/modal';
import { formatCurrency } from '@/lib/utils';
import type { Contract, Customer, StorageUnit } from '@/types';

const contractSchema = z.object({
  customer_id: z.string().min(1, 'Seleccione un cliente'),
  unit_id: z.string().min(1, 'Seleccione una unidad'),
  start_date: z.string().min(1, 'La fecha de inicio es requerida'),
  end_date: z.string().optional().nullable(),
  monthly_rate: z.coerce.number().min(0, 'La tarifa debe ser mayor o igual a 0'),
  deposit_amount: z.coerce.number().min(0).default(0),
  billing_cycle: z.enum(['monthly', 'quarterly', 'semi_annual', 'annual']).default('monthly'),
  billing_day: z.coerce.number().min(1).max(28).default(1),
  grace_period_days: z.coerce.number().min(0).default(5),
  late_fee_amount: z.coerce.number().min(0).default(0),
  auto_renew: z.boolean().default(true),
  discount_percent: z.coerce.number().min(0).max(100).optional().nullable(),
  discount_reason: z.string().max(255).optional().nullable(),
  access_code: z.string().max(50).optional().nullable(),
  access_hours: z.string().max(100).optional().nullable(),
  special_terms: z.string().max(2000).optional().nullable(),
  internal_notes: z.string().max(2000).optional().nullable(),
});

type ContractFormData = z.infer<typeof contractSchema>;

interface ContractFormProps {
  contract?: Contract | null;
  onSubmit: (data: ContractFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function ContractForm({ contract, onSubmit, onCancel, isLoading }: ContractFormProps) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [units, setUnits] = useState<StorageUnit[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [selectedUnit, setSelectedUnit] = useState<StorageUnit | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ContractFormData>({
    resolver: zodResolver(contractSchema),
    defaultValues: {
      billing_cycle: 'monthly',
      billing_day: 1,
      grace_period_days: 5,
      late_fee_amount: 0,
      deposit_amount: 0,
      auto_renew: true,
    },
  });

  const unitId = watch('unit_id');
  const monthlyRate = watch('monthly_rate');
  const discountPercent = watch('discount_percent');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (contract) {
      reset({
        customer_id: contract.customer_id,
        unit_id: contract.unit_id,
        start_date: contract.start_date,
        end_date: contract.end_date,
        monthly_rate: contract.monthly_rate,
        deposit_amount: contract.deposit_amount,
        billing_cycle: contract.billing_cycle as any,
        billing_day: contract.billing_day,
        grace_period_days: contract.grace_period_days,
        late_fee_amount: contract.late_fee_amount,
        auto_renew: contract.auto_renew,
        discount_percent: contract.discount_percent,
        discount_reason: contract.discount_reason,
        access_code: contract.access_code,
        access_hours: contract.access_hours,
        special_terms: contract.special_terms,
        internal_notes: contract.internal_notes,
      });
    }
  }, [contract, reset]);

  useEffect(() => {
    if (unitId) {
      const unit = units.find(u => u.id === unitId);
      setSelectedUnit(unit || null);
      if (unit && !contract) {
        setValue('monthly_rate', unit.monthly_rate);
        if (unit.deposit_amount) {
          setValue('deposit_amount', unit.deposit_amount);
        }
      }
    }
  }, [unitId, units, contract, setValue]);

  async function loadData() {
    try {
      const [customersData, unitsData] = await Promise.all([
        api.getCustomers({ limit: 1000 }),
        contract ? api.getStorageUnits({ limit: 1000 }) : api.getAvailableUnits(),
      ]);
      setCustomers(customersData.items);
      setUnits(unitsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoadingData(false);
    }
  }

  const effectiveRate = monthlyRate && discountPercent
    ? monthlyRate * (1 - discountPercent / 100)
    : monthlyRate;

  if (loadingData) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-6">
        {/* Customer & Unit Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select
            label="Cliente"
            options={customers.map(c => ({ value: c.id, label: c.display_name }))}
            placeholder="Seleccione un cliente..."
            error={errors.customer_id?.message}
            disabled={!!contract}
            {...register('customer_id')}
          />
          <Select
            label="Unidad"
            options={units.map(u => ({
              value: u.id,
              label: `${u.unit_number} - ${formatCurrency(u.monthly_rate, 'CRC')}/mes`,
            }))}
            placeholder="Seleccione una unidad..."
            error={errors.unit_id?.message}
            disabled={!!contract}
            {...register('unit_id')}
          />
        </div>

        {/* Unit Info */}
        {selectedUnit && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Informacion de la Unidad</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Tipo:</span>
                <p className="font-medium">{selectedUnit.unit_type}</p>
              </div>
              <div>
                <span className="text-gray-500">Tamaño:</span>
                <p className="font-medium">{selectedUnit.area_sqm ? `${selectedUnit.area_sqm} m²` : '-'}</p>
              </div>
              <div>
                <span className="text-gray-500">Edificio:</span>
                <p className="font-medium">{selectedUnit.building || '-'}</p>
              </div>
              <div>
                <span className="text-gray-500">Piso:</span>
                <p className="font-medium">{selectedUnit.floor ?? '-'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Dates */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Fecha de Inicio"
            type="date"
            error={errors.start_date?.message}
            {...register('start_date')}
          />
          <Input
            label="Fecha de Fin (opcional)"
            type="date"
            helperText="Deje vacio para contrato mes a mes"
            {...register('end_date')}
          />
        </div>

        {/* Pricing */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Facturacion</h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Tarifa Mensual"
              type="number"
              min={0}
              step="0.01"
              error={errors.monthly_rate?.message}
              {...register('monthly_rate')}
            />
            <Input
              label="Deposito"
              type="number"
              min={0}
              step="0.01"
              {...register('deposit_amount')}
            />
            <Select
              label="Ciclo de Facturacion"
              options={[
                { value: 'monthly', label: 'Mensual' },
                { value: 'quarterly', label: 'Trimestral' },
                { value: 'semi_annual', label: 'Semestral' },
                { value: 'annual', label: 'Anual' },
              ]}
              {...register('billing_cycle')}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <Input
              label="Dia de Facturacion"
              type="number"
              min={1}
              max={28}
              {...register('billing_day')}
            />
            <Input
              label="Dias de Gracia"
              type="number"
              min={0}
              {...register('grace_period_days')}
            />
            <Input
              label="Cargo por Mora"
              type="number"
              min={0}
              step="0.01"
              {...register('late_fee_amount')}
            />
          </div>
        </div>

        {/* Discount */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Descuento (%)"
            type="number"
            min={0}
            max={100}
            {...register('discount_percent')}
          />
          <Input
            label="Razon del Descuento"
            placeholder="Ej: Promocion de apertura"
            {...register('discount_reason')}
          />
        </div>

        {discountPercent && discountPercent > 0 && (
          <div className="p-3 bg-success-50 text-success-700 rounded-lg text-sm">
            Tarifa efectiva: <strong>{formatCurrency(effectiveRate || 0, 'CRC')}/mes</strong>
            {' '}({discountPercent}% de descuento)
          </div>
        )}

        {/* Access */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Acceso</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Codigo de Acceso"
              placeholder="Ej: 1234"
              {...register('access_code')}
            />
            <Input
              label="Horario de Acceso"
              placeholder="Ej: 24/7 o 6am-10pm"
              {...register('access_hours')}
            />
          </div>
        </div>

        {/* Options */}
        <div className="space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('auto_renew')}
            />
            <span className="text-sm text-gray-700">Renovacion automatica al vencer</span>
          </label>
        </div>

        {/* Notes */}
        <Textarea
          label="Terminos Especiales (opcional)"
          placeholder="Condiciones especiales del contrato..."
          {...register('special_terms')}
        />

        <Textarea
          label="Notas Internas (opcional)"
          placeholder="Notas visibles solo para el personal..."
          {...register('internal_notes')}
        />
      </div>

      <ModalFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isLoading}>
          {contract ? 'Guardar Cambios' : 'Crear Contrato'}
        </Button>
      </ModalFooter>
    </form>
  );
}
