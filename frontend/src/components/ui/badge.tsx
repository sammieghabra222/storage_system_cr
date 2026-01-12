'use client';

import { type HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-gray-100 text-gray-700',
      success: 'bg-success-50 text-success-600',
      warning: 'bg-warning-50 text-warning-600',
      danger: 'bg-danger-50 text-danger-600',
      info: 'bg-primary-50 text-primary-600',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
          variants[variant],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

// Status badge helper
export function getStatusBadgeVariant(status: string): BadgeProps['variant'] {
  const statusMap: Record<string, BadgeProps['variant']> = {
    // Unit statuses
    available: 'success',
    occupied: 'info',
    reserved: 'warning',
    maintenance: 'default',
    // Contract statuses
    draft: 'default',
    active: 'success',
    expired: 'warning',
    terminated: 'danger',
    suspended: 'danger',
    // Invoice statuses
    sent: 'info',
    paid: 'success',
    overdue: 'danger',
    cancelled: 'default',
    partial: 'warning',
    // Payment statuses
    pending: 'warning',
    confirmed: 'success',
    failed: 'danger',
  };

  return statusMap[status] || 'default';
}
