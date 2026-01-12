'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { ModalFooter } from '@/components/ui/modal';
import type { Customer } from '@/types';

const customerSchema = z.object({
  customer_type: z.enum(['individual', 'business']),
  cedula: z.string().max(20).optional().nullable(),
  cedula_juridica: z.string().max(20).optional().nullable(),
  first_name: z.string().min(1, 'El nombre es requerido').max(100),
  last_name: z.string().max(100).optional().nullable(),
  company_name: z.string().max(255).optional().nullable(),
  email: z.string().email('Ingrese un correo valido'),
  phone: z.string().min(1, 'El telefono es requerido').max(20),
  phone_secondary: z.string().max(20).optional().nullable(),
  address: z.string().max(500).optional().nullable(),
  city: z.string().max(100).optional().nullable(),
  province: z.string().max(100).optional().nullable(),
  postal_code: z.string().max(20).optional().nullable(),
  country: z.string().max(2).default('CR'),
  emergency_contact_name: z.string().max(200).optional().nullable(),
  emergency_contact_phone: z.string().max(20).optional().nullable(),
  preferred_language: z.string().default('es'),
  accepts_email_notifications: z.boolean().default(true),
  accepts_sms_notifications: z.boolean().default(false),
  notes: z.string().max(2000).optional().nullable(),
});

type CustomerFormData = z.infer<typeof customerSchema>;

interface CustomerFormProps {
  customer?: Customer | null;
  onSubmit: (data: CustomerFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function CustomerForm({ customer, onSubmit, onCancel, isLoading }: CustomerFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<CustomerFormData>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      customer_type: 'individual',
      country: 'CR',
      preferred_language: 'es',
      accepts_email_notifications: true,
      accepts_sms_notifications: false,
    },
  });

  const customerType = watch('customer_type');

  useEffect(() => {
    if (customer) {
      reset({
        customer_type: customer.customer_type as 'individual' | 'business',
        cedula: customer.cedula,
        cedula_juridica: customer.cedula_juridica,
        first_name: customer.first_name,
        last_name: customer.last_name,
        company_name: customer.company_name,
        email: customer.email,
        phone: customer.phone,
        phone_secondary: customer.phone_secondary,
        address: customer.address,
        city: customer.city,
        province: customer.province,
        postal_code: customer.postal_code,
        country: customer.country,
        emergency_contact_name: customer.emergency_contact_name,
        emergency_contact_phone: customer.emergency_contact_phone,
        preferred_language: customer.preferred_language,
        accepts_email_notifications: customer.accepts_email_notifications,
        accepts_sms_notifications: customer.accepts_sms_notifications,
        notes: customer.notes,
      });
    }
  }, [customer, reset]);

  const provinces = [
    { value: 'San Jose', label: 'San Jose' },
    { value: 'Alajuela', label: 'Alajuela' },
    { value: 'Cartago', label: 'Cartago' },
    { value: 'Heredia', label: 'Heredia' },
    { value: 'Guanacaste', label: 'Guanacaste' },
    { value: 'Puntarenas', label: 'Puntarenas' },
    { value: 'Limon', label: 'Limon' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-6">
        {/* Customer Type */}
        <Select
          label="Tipo de Cliente"
          options={[
            { value: 'individual', label: 'Persona Fisica' },
            { value: 'business', label: 'Empresa' },
          ]}
          error={errors.customer_type?.message}
          {...register('customer_type')}
        />

        {/* Identification */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {customerType === 'individual' ? (
            <Input
              label="Cedula"
              placeholder="1-0234-0567"
              error={errors.cedula?.message}
              {...register('cedula')}
            />
          ) : (
            <Input
              label="Cedula Juridica"
              placeholder="3-101-123456"
              error={errors.cedula_juridica?.message}
              {...register('cedula_juridica')}
            />
          )}
        </div>

        {/* Name */}
        {customerType === 'business' && (
          <Input
            label="Nombre de la Empresa"
            error={errors.company_name?.message}
            {...register('company_name')}
          />
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label={customerType === 'business' ? 'Nombre del Contacto' : 'Nombre'}
            error={errors.first_name?.message}
            {...register('first_name')}
          />
          <Input
            label="Apellido"
            error={errors.last_name?.message}
            {...register('last_name')}
          />
        </div>

        {/* Contact */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Correo Electronico"
            type="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Input
            label="Telefono"
            placeholder="8888-8888"
            error={errors.phone?.message}
            {...register('phone')}
          />
        </div>

        <Input
          label="Telefono Secundario (opcional)"
          placeholder="2222-2222"
          {...register('phone_secondary')}
        />

        {/* Address */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Direccion</h4>

          <div className="space-y-4">
            <Input
              label="Direccion"
              placeholder="Calle, numero, referencias..."
              {...register('address')}
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Ciudad"
                {...register('city')}
              />
              <Select
                label="Provincia"
                options={provinces}
                placeholder="Seleccione..."
                {...register('province')}
              />
              <Input
                label="Codigo Postal"
                {...register('postal_code')}
              />
            </div>
          </div>
        </div>

        {/* Emergency Contact */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Contacto de Emergencia (opcional)</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nombre"
              {...register('emergency_contact_name')}
            />
            <Input
              label="Telefono"
              placeholder="8888-8888"
              {...register('emergency_contact_phone')}
            />
          </div>
        </div>

        {/* Preferences */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-4">Preferencias</h4>

          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                {...register('accepts_email_notifications')}
              />
              <span className="text-sm text-gray-700">Recibir notificaciones por correo</span>
            </label>

            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                {...register('accepts_sms_notifications')}
              />
              <span className="text-sm text-gray-700">Recibir notificaciones por SMS</span>
            </label>
          </div>
        </div>

        {/* Notes */}
        <Textarea
          label="Notas (opcional)"
          placeholder="Informacion adicional sobre el cliente..."
          {...register('notes')}
        />
      </div>

      <ModalFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isLoading}>
          {customer ? 'Guardar Cambios' : 'Crear Cliente'}
        </Button>
      </ModalFooter>
    </form>
  );
}
