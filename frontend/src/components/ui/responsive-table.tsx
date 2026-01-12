'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent } from './card';

export interface ResponsiveColumn<T> {
  key: string;
  header: string;
  /** Priority determines visibility on mobile. 1 = always show, higher = hide on smaller screens */
  priority?: 1 | 2 | 3;
  className?: string;
  /** Used in mobile card view */
  mobileLabel?: string;
  render?: (item: T, index: number) => React.ReactNode;
}

export interface ResponsiveTableProps<T> {
  data: T[];
  columns: ResponsiveColumn<T>[];
  keyExtractor: (item: T) => string;
  pageSize?: number;
  showPagination?: boolean;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  loading?: boolean;
  onRowClick?: (item: T) => void;
  /** Actions column content - shows as last column on desktop, bottom of card on mobile */
  renderActions?: (item: T) => React.ReactNode;
  /** Primary content for mobile card header */
  renderMobileHeader?: (item: T) => React.ReactNode;
  /** Secondary content for mobile card */
  renderMobileSubheader?: (item: T) => React.ReactNode;
}

export function ResponsiveTable<T extends Record<string, any>>({
  data,
  columns,
  keyExtractor,
  pageSize = 10,
  showPagination = true,
  emptyMessage = 'No hay datos para mostrar',
  emptyIcon,
  loading = false,
  onRowClick,
  renderActions,
  renderMobileHeader,
  renderMobileSubheader,
}: ResponsiveTableProps<T>) {
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  // Pagination
  const totalPages = Math.ceil(data.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedData = showPagination ? data.slice(startIndex, endIndex) : data;

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Get columns by priority for mobile view
  const priorityColumns = columns.filter(c => c.priority === 1 || !c.priority);
  const secondaryColumns = columns.filter(c => c.priority && c.priority > 1);

  // Helper to get nested value
  const getValue = (item: T, key: string) => {
    return key.split('.').reduce((obj, k) => obj?.[k], item as any);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {emptyIcon && <div className="mb-4">{emptyIcon}</div>}
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-y border-gray-200">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-4 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${column.className || ''}`}
                >
                  {column.header}
                </th>
              ))}
              {renderActions && (
                <th className="px-4 lg:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {paginatedData.map((item, index) => (
              <tr
                key={keyExtractor(item)}
                className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : 'hover:bg-gray-50'}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={`px-4 lg:px-6 py-4 whitespace-nowrap text-sm ${column.className || ''}`}
                  >
                    {column.render
                      ? column.render(item, startIndex + index)
                      : getValue(item, column.key)}
                  </td>
                ))}
                {renderActions && (
                  <td className="px-4 lg:px-6 py-4 whitespace-nowrap text-right">
                    {renderActions(item)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-3">
        {paginatedData.map((item, index) => {
          const id = keyExtractor(item);
          const isExpanded = expandedItems.has(id);

          return (
            <Card
              key={id}
              className={onRowClick ? 'cursor-pointer' : ''}
              onClick={() => onRowClick?.(item)}
            >
              <CardContent className="p-4">
                {/* Mobile Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    {renderMobileHeader ? (
                      renderMobileHeader(item)
                    ) : (
                      <div className="font-medium text-gray-900 truncate">
                        {priorityColumns[0]?.render
                          ? priorityColumns[0].render(item, index)
                          : getValue(item, priorityColumns[0]?.key || '')}
                      </div>
                    )}
                    {renderMobileSubheader && (
                      <div className="text-sm text-gray-500 mt-0.5">
                        {renderMobileSubheader(item)}
                      </div>
                    )}
                  </div>
                  {renderActions && (
                    <div className="flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                      {renderActions(item)}
                    </div>
                  )}
                </div>

                {/* Priority Fields (always visible) */}
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {priorityColumns.slice(1).map((column) => (
                    <div key={column.key}>
                      <span className="text-xs text-gray-500">
                        {column.mobileLabel || column.header}
                      </span>
                      <div className="text-sm font-medium text-gray-900">
                        {column.render
                          ? column.render(item, index)
                          : getValue(item, column.key) || '-'}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Expandable Secondary Fields */}
                {secondaryColumns.length > 0 && (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(id);
                      }}
                      className="mt-3 flex items-center justify-center w-full py-2 text-xs text-gray-500 hover:text-gray-700 border-t border-gray-100"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="w-4 h-4 mr-1" />
                          Menos detalles
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4 mr-1" />
                          Mas detalles
                        </>
                      )}
                    </button>

                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-2 gap-2">
                        {secondaryColumns.map((column) => (
                          <div key={column.key}>
                            <span className="text-xs text-gray-500">
                              {column.mobileLabel || column.header}
                            </span>
                            <div className="text-sm text-gray-900">
                              {column.render
                                ? column.render(item, index)
                                : getValue(item, column.key) || '-'}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-4 py-4 border-t border-gray-200 mt-4">
          <div className="text-sm text-gray-500 text-center sm:text-left">
            {startIndex + 1}-{Math.min(endIndex, data.length)} de {data.length}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="w-4 h-4" />
              <span className="sr-only sm:not-sr-only sm:ml-1">Anterior</span>
            </Button>

            <span className="text-sm text-gray-600 px-2">
              {currentPage} / {totalPages}
            </span>

            <Button
              variant="outline"
              size="sm"
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              <span className="sr-only sm:not-sr-only sm:mr-1">Siguiente</span>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
