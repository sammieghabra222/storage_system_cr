'use client';

import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label?: string;
    isPositive?: boolean;
  };
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'gray';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const colorStyles = {
  primary: {
    bg: 'bg-blue-50',
    icon: 'text-blue-600',
    trend: 'text-blue-600',
  },
  success: {
    bg: 'bg-green-50',
    icon: 'text-green-600',
    trend: 'text-green-600',
  },
  warning: {
    bg: 'bg-amber-50',
    icon: 'text-amber-600',
    trend: 'text-amber-600',
  },
  danger: {
    bg: 'bg-red-50',
    icon: 'text-red-600',
    trend: 'text-red-600',
  },
  gray: {
    bg: 'bg-gray-50',
    icon: 'text-gray-600',
    trend: 'text-gray-600',
  },
};

const sizeStyles = {
  sm: {
    padding: 'p-3',
    iconSize: 'w-5 h-5',
    iconPadding: 'p-2',
    labelSize: 'text-xs',
    valueSize: 'text-lg',
  },
  md: {
    padding: 'p-4',
    iconSize: 'w-6 h-6',
    iconPadding: 'p-3',
    labelSize: 'text-sm',
    valueSize: 'text-2xl',
  },
  lg: {
    padding: 'p-6',
    iconSize: 'w-8 h-8',
    iconPadding: 'p-4',
    labelSize: 'text-base',
    valueSize: 'text-3xl',
  },
};

export function StatsCard({
  label,
  value,
  icon: Icon,
  trend,
  color = 'primary',
  size = 'md',
  className = '',
}: StatsCardProps) {
  const colors = colorStyles[color];
  const sizes = sizeStyles[size];

  return (
    <Card className={className}>
      <CardContent className={sizes.padding}>
        <div className="flex items-center gap-4">
          {Icon && (
            <div className={`${sizes.iconPadding} rounded-lg ${colors.bg}`}>
              <Icon className={`${sizes.iconSize} ${colors.icon}`} />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className={`${sizes.labelSize} text-gray-600 truncate`}>{label}</p>
            <div className="flex items-baseline gap-2">
              <p className={`${sizes.valueSize} font-bold text-gray-900`}>
                {value}
              </p>
              {trend && (
                <span
                  className={`text-xs font-medium ${
                    trend.isPositive !== false ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {trend.isPositive !== false ? '+' : ''}
                  {trend.value}%
                  {trend.label && (
                    <span className="text-gray-400 ml-1">{trend.label}</span>
                  )}
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
