'use client';

import { useMemo } from 'react';

export interface BarChartData {
  label: string;
  value: number;
  color?: string;
}

interface BarChartProps {
  data: BarChartData[];
  height?: number;
  showValues?: boolean;
  showLabels?: boolean;
  horizontal?: boolean;
  formatValue?: (value: number) => string;
  className?: string;
}

const DEFAULT_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#06b6d4', // cyan
  '#f97316', // orange
  '#ec4899', // pink
];

export function BarChart({
  data,
  height = 200,
  showValues = true,
  showLabels = true,
  horizontal = false,
  formatValue = (v) => v.toLocaleString(),
  className = '',
}: BarChartProps) {
  const maxValue = useMemo(() => {
    return Math.max(...data.map((d) => d.value), 1);
  }, [data]);

  if (horizontal) {
    return (
      <div className={`space-y-3 ${className}`}>
        {data.map((item, index) => {
          const percentage = (item.value / maxValue) * 100;
          const color = item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];

          return (
            <div key={index} className="space-y-1">
              {showLabels && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">{item.label}</span>
                  {showValues && (
                    <span className="font-medium text-gray-900">
                      {formatValue(item.value)}
                    </span>
                  )}
                </div>
              )}
              <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className}`} style={{ height }}>
      <div className="flex-1 flex items-end justify-around gap-2">
        {data.map((item, index) => {
          const percentage = (item.value / maxValue) * 100;
          const color = item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];

          return (
            <div
              key={index}
              className="flex flex-col items-center flex-1 max-w-16"
            >
              {showValues && (
                <span className="text-xs font-medium text-gray-600 mb-1">
                  {formatValue(item.value)}
                </span>
              )}
              <div
                className="w-full rounded-t-md transition-all duration-500 ease-out min-h-[4px]"
                style={{
                  height: `${Math.max(percentage, 2)}%`,
                  backgroundColor: color,
                }}
              />
            </div>
          );
        })}
      </div>
      {showLabels && (
        <div className="flex justify-around gap-2 mt-2 pt-2 border-t border-gray-100">
          {data.map((item, index) => (
            <span
              key={index}
              className="text-xs text-gray-500 text-center flex-1 max-w-16 truncate"
              title={item.label}
            >
              {item.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
