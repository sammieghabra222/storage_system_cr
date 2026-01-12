'use client';

import { useMemo } from 'react';

export interface DonutChartData {
  label: string;
  value: number;
  color?: string;
}

interface DonutChartProps {
  data: DonutChartData[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string | number;
  showLegend?: boolean;
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

export function DonutChart({
  data,
  size = 160,
  thickness = 24,
  centerLabel,
  centerValue,
  showLegend = true,
  formatValue = (v) => v.toLocaleString(),
  className = '',
}: DonutChartProps) {
  const total = useMemo(() => {
    return data.reduce((sum, item) => sum + item.value, 0);
  }, [data]);

  const segments = useMemo(() => {
    let currentAngle = -90; // Start from top
    return data.map((item, index) => {
      const percentage = total > 0 ? (item.value / total) * 100 : 0;
      const angle = (percentage / 100) * 360;
      const startAngle = currentAngle;
      currentAngle += angle;

      return {
        ...item,
        percentage,
        startAngle,
        endAngle: currentAngle,
        color: item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
      };
    });
  }, [data, total]);

  const radius = size / 2;
  const innerRadius = radius - thickness;

  // Create SVG path for each segment
  const createArcPath = (startAngle: number, endAngle: number) => {
    const start = polarToCartesian(radius, radius, radius - 1, endAngle);
    const end = polarToCartesian(radius, radius, radius - 1, startAngle);
    const innerStart = polarToCartesian(radius, radius, innerRadius, endAngle);
    const innerEnd = polarToCartesian(radius, radius, innerRadius, startAngle);

    const largeArcFlag = endAngle - startAngle <= 180 ? 0 : 1;

    return [
      'M', start.x, start.y,
      'A', radius - 1, radius - 1, 0, largeArcFlag, 0, end.x, end.y,
      'L', innerEnd.x, innerEnd.y,
      'A', innerRadius, innerRadius, 0, largeArcFlag, 1, innerStart.x, innerStart.y,
      'Z',
    ].join(' ');
  };

  function polarToCartesian(cx: number, cy: number, r: number, angle: number) {
    const rad = (angle * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  }

  return (
    <div className={`flex items-center gap-6 ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background circle */}
          <circle
            cx={radius}
            cy={radius}
            r={radius - thickness / 2}
            fill="none"
            stroke="#f3f4f6"
            strokeWidth={thickness}
          />
          {/* Segments */}
          {segments.map((segment, index) => {
            if (segment.percentage === 0) return null;
            // Handle full circle case
            if (segment.percentage >= 99.9) {
              return (
                <circle
                  key={index}
                  cx={radius}
                  cy={radius}
                  r={radius - thickness / 2}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={thickness}
                />
              );
            }
            return (
              <path
                key={index}
                d={createArcPath(segment.startAngle, segment.endAngle)}
                fill={segment.color}
                className="transition-all duration-500"
              />
            );
          })}
        </svg>
        {/* Center content */}
        {(centerLabel || centerValue) && (
          <div
            className="absolute inset-0 flex flex-col items-center justify-center"
            style={{ padding: thickness }}
          >
            {centerValue !== undefined && (
              <span className="text-2xl font-bold text-gray-900">
                {centerValue}
              </span>
            )}
            {centerLabel && (
              <span className="text-xs text-gray-500 text-center">
                {centerLabel}
              </span>
            )}
          </div>
        )}
      </div>

      {showLegend && (
        <div className="flex flex-col gap-2">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: segment.color }}
              />
              <div className="flex flex-col">
                <span className="text-sm text-gray-600">{segment.label}</span>
                <span className="text-xs text-gray-400">
                  {formatValue(segment.value)} ({segment.percentage.toFixed(1)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
