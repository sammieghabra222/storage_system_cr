'use client';

import { ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: {
    value: number;
    period?: string;
  };
  chart?: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  change,
  chart,
  footer,
  className = '',
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (!change) return null;
    if (change.value > 0) return <TrendingUp className="w-4 h-4" />;
    if (change.value < 0) return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getTrendColor = () => {
    if (!change) return 'text-gray-500';
    if (change.value > 0) return 'text-green-600';
    if (change.value < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-gray-900">{value}</span>
              {change && (
                <div className={`flex items-center gap-1 ${getTrendColor()}`}>
                  {getTrendIcon()}
                  <span className="text-sm font-medium">
                    {change.value > 0 ? '+' : ''}
                    {change.value}%
                  </span>
                </div>
              )}
            </div>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
            {change?.period && (
              <p className="text-xs text-gray-400">{change.period}</p>
            )}
          </div>

          {chart && <div className="mt-4">{chart}</div>}

          {footer && (
            <div className="pt-3 border-t border-gray-100">{footer}</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
