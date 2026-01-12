'use client';

import { useMemo } from 'react';

export interface AreaChartData {
  label: string;
  value: number;
}

interface AreaChartProps {
  data: AreaChartData[];
  height?: number;
  color?: string;
  gradientFrom?: string;
  gradientTo?: string;
  showDots?: boolean;
  showLabels?: boolean;
  showValues?: boolean;
  formatValue?: (value: number) => string;
  className?: string;
}

export function AreaChart({
  data,
  height = 160,
  color = '#3b82f6',
  gradientFrom,
  gradientTo,
  showDots = true,
  showLabels = true,
  showValues = false,
  formatValue = (v) => v.toLocaleString(),
  className = '',
}: AreaChartProps) {
  const chartData = useMemo(() => {
    if (data.length === 0) return { points: '', areaPath: '', minValue: 0, maxValue: 0 };

    const values = data.map((d) => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;

    const padding = 20;
    const chartWidth = 100;
    const chartHeight = 100;

    const pointsData = data.map((item, index) => {
      const x = (index / (data.length - 1 || 1)) * (chartWidth - padding * 2) + padding;
      const y = chartHeight - padding - ((item.value - minValue) / range) * (chartHeight - padding * 2);
      return { x, y, ...item };
    });

    const points = pointsData.map((p) => `${p.x},${p.y}`).join(' ');

    // Create area path
    const areaPath = [
      `M ${pointsData[0]?.x || padding},${chartHeight - padding}`,
      `L ${pointsData[0]?.x || padding},${pointsData[0]?.y || chartHeight - padding}`,
      ...pointsData.slice(1).map((p) => `L ${p.x},${p.y}`),
      `L ${pointsData[pointsData.length - 1]?.x || chartWidth - padding},${chartHeight - padding}`,
      'Z',
    ].join(' ');

    return { points, areaPath, pointsData, minValue, maxValue };
  }, [data]);

  const gradientId = useMemo(() => `area-gradient-${Math.random().toString(36).substr(2, 9)}`, []);

  if (data.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <span className="text-gray-400 text-sm">No data available</span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className}`}>
      <div style={{ height }}>
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop
                offset="0%"
                stopColor={gradientFrom || color}
                stopOpacity="0.3"
              />
              <stop
                offset="100%"
                stopColor={gradientTo || color}
                stopOpacity="0.05"
              />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1="20" y1="20" x2="20" y2="80" stroke="#e5e7eb" strokeWidth="0.5" />
          <line x1="20" y1="80" x2="80" y2="80" stroke="#e5e7eb" strokeWidth="0.5" />
          <line x1="20" y1="50" x2="80" y2="50" stroke="#e5e7eb" strokeWidth="0.3" strokeDasharray="2,2" />

          {/* Area fill */}
          <path
            d={chartData.areaPath}
            fill={`url(#${gradientId})`}
            className="transition-all duration-500"
          />

          {/* Line */}
          <polyline
            points={chartData.points}
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
            className="transition-all duration-500"
          />

          {/* Dots */}
          {showDots &&
            chartData.pointsData?.map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r="1.5"
                fill="white"
                stroke={color}
                strokeWidth="1"
                vectorEffect="non-scaling-stroke"
              />
            ))}
        </svg>
      </div>

      {/* Labels */}
      {showLabels && (
        <div className="flex justify-between px-2 mt-2">
          {data.map((item, index) => (
            <div key={index} className="flex flex-col items-center">
              <span className="text-xs text-gray-500">{item.label}</span>
              {showValues && (
                <span className="text-xs font-medium text-gray-700">
                  {formatValue(item.value)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
