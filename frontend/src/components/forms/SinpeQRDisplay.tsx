'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { Smartphone, Copy, Check, Loader2, AlertCircle, QrCode } from 'lucide-react';
import { api } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import type { SinpeQRResponse } from '@/types';

interface SinpeQRDisplayProps {
  amount: number;
  currency?: string;
  invoiceId?: string;
  description?: string;
  onClose?: () => void;
}

export function SinpeQRDisplay({
  amount,
  currency = 'CRC',
  invoiceId,
  description,
  onClose,
}: SinpeQRDisplayProps) {
  const t = useTranslations('payments');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [qrData, setQrData] = useState<SinpeQRResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadQRCode();
  }, []);

  async function loadQRCode() {
    try {
      setLoading(true);
      setError(null);

      let result: SinpeQRResponse;
      if (invoiceId) {
        result = await api.generateInvoiceSinpeQR(invoiceId);
      } else {
        result = await api.generateSinpeQR({
          amount,
          description,
        });
      }

      setQrData(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'No se pudo generar el codigo QR');
    } finally {
      setLoading(false);
    }
  }

  async function copyPhoneNumber() {
    if (!qrData?.phone_number) return;

    try {
      await navigator.clipboard.writeText(qrData.phone_number);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = qrData.phone_number;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
            <p className="text-gray-600">Generando codigo QR...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center gap-4">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Error al generar QR
              </h3>
              <p className="text-red-600 mt-1">{error}</p>
            </div>

            <div className="flex gap-3 mt-4">
              <Button variant="outline" onClick={onClose}>
                Cerrar
              </Button>
              <Button onClick={loadQRCode}>
                Intentar de nuevo
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Smartphone className="w-5 h-5" />
          Pago con SINPE Movil
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Amount */}
        <div className="text-center p-4 bg-primary-50 rounded-lg">
          <p className="text-sm text-gray-600">Monto a pagar</p>
          <p className="text-3xl font-bold text-primary-600">
            {formatCurrency(qrData?.amount || amount, currency)}
          </p>
        </div>

        {/* QR Code */}
        <div className="flex justify-center">
          {qrData?.qr_base64 ? (
            <img
              src={`data:image/png;base64,${qrData.qr_base64}`}
              alt="SINPE QR Code"
              className="w-48 h-48"
            />
          ) : (
            <div className="w-48 h-48 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center">
              <QrCode className="w-12 h-12 text-gray-400 mb-2" />
              <p className="text-xs text-gray-500 text-center px-4">
                Escanee el codigo QR con su app bancaria
              </p>
            </div>
          )}
        </div>

        {/* QR Data for client-side rendering */}
        {!qrData?.qr_base64 && qrData?.qr_data && (
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-2">
              Si el QR no aparece, use este codigo:
            </p>
            <code className="block p-3 bg-gray-100 rounded text-xs break-all">
              {qrData.qr_data}
            </code>
          </div>
        )}

        {/* Phone number for manual transfer */}
        <div className="border-t pt-4">
          <p className="text-sm text-gray-600 text-center mb-3">
            O transfiera manualmente al numero:
          </p>
          <div className="flex items-center justify-center gap-2">
            <span className="text-2xl font-mono font-bold text-gray-900">
              {qrData?.phone_number}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={copyPhoneNumber}
              className="shrink-0"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className="text-sm text-gray-500 text-center mt-2">
            {qrData?.recipient_name}
          </p>
        </div>

        {/* Description / Invoice reference */}
        {(qrData?.description || qrData?.invoice_number) && (
          <div className="text-center text-sm text-gray-500">
            <p>Referencia: {qrData?.invoice_number || qrData?.description}</p>
          </div>
        )}

        {/* Instructions */}
        <Alert variant="info">
          <div className="text-sm">
            <p className="font-medium mb-1">Instrucciones:</p>
            <ol className="list-decimal list-inside space-y-1 text-gray-600">
              <li>Abra su aplicacion bancaria</li>
              <li>Seleccione SINPE Movil</li>
              <li>Escanee el codigo QR o ingrese el numero</li>
              <li>Confirme el monto y complete la transferencia</li>
              <li>Guarde el comprobante</li>
            </ol>
          </div>
        </Alert>

        {/* Actions */}
        <div className="flex justify-center pt-2">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
