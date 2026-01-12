'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { CreditCard, Lock, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert } from '@/components/ui/alert';
import type { CardPaymentIntent, CardPaymentStatus, Customer } from '@/types';

interface CardPaymentFormProps {
  customer: Customer;
  amount: number;
  currency?: string;
  invoiceId?: string;
  description?: string;
  onSuccess?: (result: CardPaymentStatus) => void;
  onCancel?: () => void;
}

type PaymentStep = 'init' | 'card_input' | 'processing' | 'success' | 'error';

export function CardPaymentForm({
  customer,
  amount,
  currency = 'CRC',
  invoiceId,
  description,
  onSuccess,
  onCancel,
}: CardPaymentFormProps) {
  const t = useTranslations('payments');

  const [step, setStep] = useState<PaymentStep>('init');
  const [paymentIntent, setPaymentIntent] = useState<CardPaymentIntent | null>(null);
  const [paymentResult, setPaymentResult] = useState<CardPaymentStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Card form state (for sandbox/demo mode)
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvc, setCvc] = useState('');
  const [cardholderName, setCardholderName] = useState('');

  // Create payment intent on mount
  useEffect(() => {
    createPaymentIntent();
  }, []);

  async function createPaymentIntent() {
    try {
      setStep('init');
      setError(null);

      const intent = await api.createCardPaymentIntent({
        customer_id: customer.id,
        invoice_id: invoiceId,
        amount,
        currency,
        description,
      });

      setPaymentIntent(intent);
      setStep('card_input');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'No se pudo iniciar el pago');
      setStep('error');
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!paymentIntent) {
      setError('No hay intento de pago activo');
      return;
    }

    // Basic validation
    if (!cardNumber || !expiry || !cvc) {
      setError('Por favor complete todos los campos');
      return;
    }

    try {
      setStep('processing');
      setError(null);

      // In sandbox mode, use card number as payment_method_id
      // In production with Stripe, you'd use Stripe.js to create a PaymentMethod
      const cleanCardNumber = cardNumber.replace(/\s/g, '');

      const result = await api.confirmCardPayment({
        intent_id: paymentIntent.intent_id,
        payment_method_id: cleanCardNumber,
      });

      if (result.success) {
        setPaymentResult(result);
        setStep('success');
        onSuccess?.(result);
      } else {
        setError(result.error_message || 'El pago fue rechazado');
        setStep('error');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar el pago');
      setStep('error');
    }
  }

  function formatCardNumber(value: string) {
    const cleaned = value.replace(/\D/g, '');
    const chunks = cleaned.match(/.{1,4}/g);
    return chunks ? chunks.join(' ').substring(0, 19) : '';
  }

  function formatExpiry(value: string) {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return cleaned.substring(0, 2) + '/' + cleaned.substring(2, 4);
    }
    return cleaned;
  }

  function getCardBrandIcon(number: string) {
    const cleaned = number.replace(/\s/g, '');
    if (cleaned.startsWith('4')) return 'Visa';
    if (cleaned.startsWith('5')) return 'Mastercard';
    if (cleaned.startsWith('3')) return 'Amex';
    return null;
  }

  // Loading state
  if (step === 'init') {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            <p className="text-gray-600">Preparando el pago...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Success state
  if (step === 'success' && paymentResult) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center gap-4">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Pago Exitoso
              </h3>
              <p className="text-gray-600 mt-1">
                Se proceso el pago por {formatCurrency(amount, currency)}
              </p>
            </div>

            {paymentResult.card_brand && paymentResult.card_last_four && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <CreditCard className="w-4 h-4" />
                <span>
                  {paymentResult.card_brand} terminada en {paymentResult.card_last_four}
                </span>
              </div>
            )}

            <p className="text-sm text-gray-500">
              ID de transaccion: {paymentResult.transaction_id}
            </p>

            <Button onClick={onCancel} className="mt-4">
              Cerrar
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (step === 'error') {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center gap-4">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Error en el Pago
              </h3>
              <p className="text-red-600 mt-1">{error}</p>
            </div>

            <div className="flex gap-3 mt-4">
              <Button variant="outline" onClick={onCancel}>
                Cancelar
              </Button>
              <Button onClick={createPaymentIntent}>
                Intentar de nuevo
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Card input form
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="w-5 h-5" />
          Pago con Tarjeta
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Amount display */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Monto a pagar</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(amount, currency)}
            </p>
            {description && (
              <p className="text-sm text-gray-500 mt-1">{description}</p>
            )}
          </div>

          {/* Card number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Numero de tarjeta
            </label>
            <div className="relative">
              <Input
                type="text"
                value={cardNumber}
                onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                placeholder="4242 4242 4242 4242"
                maxLength={19}
                className="pl-10"
                disabled={step === 'processing'}
              />
              <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              {getCardBrandIcon(cardNumber) && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-gray-500">
                  {getCardBrandIcon(cardNumber)}
                </span>
              )}
            </div>
          </div>

          {/* Expiry and CVC */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Vencimiento
              </label>
              <Input
                type="text"
                value={expiry}
                onChange={(e) => setExpiry(formatExpiry(e.target.value))}
                placeholder="MM/AA"
                maxLength={5}
                disabled={step === 'processing'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CVC
              </label>
              <Input
                type="text"
                value={cvc}
                onChange={(e) => setCvc(e.target.value.replace(/\D/g, '').substring(0, 4))}
                placeholder="123"
                maxLength={4}
                disabled={step === 'processing'}
              />
            </div>
          </div>

          {/* Cardholder name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre en la tarjeta
            </label>
            <Input
              type="text"
              value={cardholderName}
              onChange={(e) => setCardholderName(e.target.value)}
              placeholder="JUAN PEREZ"
              disabled={step === 'processing'}
            />
          </div>

          {/* Error message */}
          {error && (
            <Alert variant="error">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </Alert>
          )}

          {/* Security notice */}
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Lock className="w-3 h-3" />
            <span>Pago seguro. Sus datos estan encriptados.</span>
          </div>

          {/* Sandbox notice */}
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-xs text-amber-800">
              <strong>Modo de prueba:</strong> Use la tarjeta 4242 4242 4242 4242
              con cualquier fecha futura y CVC para simular un pago exitoso.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={step === 'processing'}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={step === 'processing'}
              className="flex-1"
            >
              {step === 'processing' ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Procesando...
                </>
              ) : (
                `Pagar ${formatCurrency(amount, currency)}`
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
