'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/stores/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardFooter } from '@/components/ui/card';

const registerSchema = z.object({
  business_name: z.string().min(1, 'El nombre del negocio es requerido'),
  business_email: z.string().email('Ingrese un correo valido'),
  business_phone: z.string().optional(),
  first_name: z.string().min(1, 'El nombre es requerido'),
  last_name: z.string().min(1, 'El apellido es requerido'),
  email: z.string().email('Ingrese un correo valido'),
  password: z.string().min(8, 'La contrasena debe tener al menos 8 caracteres'),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Las contrasenas no coinciden',
  path: ['confirm_password'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const t = useTranslations('auth');
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setError(null);
    try {
      await registerUser({
        business_name: data.business_name,
        business_email: data.business_email,
        business_phone: data.business_phone,
        first_name: data.first_name,
        last_name: data.last_name,
        email: data.email,
        password: data.password,
        locale: 'es',
      });
      router.push('/es/dashboard');
    } catch {
      setError(t('registerError'));
    }
  };

  return (
    <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
      <Card>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4 pt-6">
            <h2 className="text-xl font-semibold text-center text-gray-900 mb-6">
              {t('createAccount')}
            </h2>

            {error && (
              <div className="p-3 rounded-lg bg-danger-50 text-danger-600 text-sm">
                {error}
              </div>
            )}

            {/* Business Info */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-700 border-b pb-2">
                Informacion del Negocio
              </h3>

              <Input
                label={t('businessName')}
                error={errors.business_name?.message}
                {...register('business_name')}
              />

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={t('businessEmail')}
                  type="email"
                  error={errors.business_email?.message}
                  {...register('business_email')}
                />
                <Input
                  label={t('businessPhone')}
                  type="tel"
                  placeholder="8888-8888"
                  {...register('business_phone')}
                />
              </div>
            </div>

            {/* Personal Info */}
            <div className="space-y-4 pt-4">
              <h3 className="text-sm font-medium text-gray-700 border-b pb-2">
                Informacion Personal
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={t('firstName')}
                  error={errors.first_name?.message}
                  {...register('first_name')}
                />
                <Input
                  label={t('lastName')}
                  error={errors.last_name?.message}
                  {...register('last_name')}
                />
              </div>

              <Input
                label={t('email')}
                type="email"
                autoComplete="email"
                error={errors.email?.message}
                {...register('email')}
              />

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label={t('password')}
                  type="password"
                  autoComplete="new-password"
                  error={errors.password?.message}
                  {...register('password')}
                />
                <Input
                  label={t('confirmPassword')}
                  type="password"
                  autoComplete="new-password"
                  error={errors.confirm_password?.message}
                  {...register('confirm_password')}
                />
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" isLoading={isLoading}>
              {t('register')}
            </Button>

            <p className="text-center text-sm text-gray-600">
              {t('hasAccount')}{' '}
              <Link href="/es/login" className="text-primary-600 hover:text-primary-500 font-medium">
                {t('login')}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
