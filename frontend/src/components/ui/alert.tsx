'use client';

import { type HTMLAttributes, forwardRef } from 'react';
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
}

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', title, children, ...props }, ref) => {
    const variants = {
      info: {
        container: 'bg-primary-50 border-primary-200 text-primary-800',
        icon: Info,
        iconColor: 'text-primary-500',
      },
      success: {
        container: 'bg-success-50 border-success-200 text-success-800',
        icon: CheckCircle,
        iconColor: 'text-success-500',
      },
      warning: {
        container: 'bg-warning-50 border-warning-200 text-warning-800',
        icon: AlertCircle,
        iconColor: 'text-warning-500',
      },
      error: {
        container: 'bg-danger-50 border-danger-200 text-danger-800',
        icon: XCircle,
        iconColor: 'text-danger-500',
      },
    };

    const { container, icon: Icon, iconColor } = variants[variant];

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-lg border p-4',
          container,
          className
        )}
        {...props}
      >
        <div className="flex gap-3">
          <Icon className={cn('w-5 h-5 flex-shrink-0', iconColor)} />
          <div>
            {title && <h4 className="font-medium mb-1">{title}</h4>}
            <div className="text-sm">{children}</div>
          </div>
        </div>
      </div>
    );
  }
);

Alert.displayName = 'Alert';
