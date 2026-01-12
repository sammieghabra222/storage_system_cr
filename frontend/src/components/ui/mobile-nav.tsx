'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Package,
  Users,
  CreditCard,
  Menu,
} from 'lucide-react';

interface MobileNavProps {
  locale?: string;
  onMenuClick?: () => void;
}

const navItems = [
  { key: 'dashboard', href: '/dashboard', icon: LayoutDashboard, label: 'Inicio' },
  { key: 'units', href: '/units', icon: Package, label: 'Unidades' },
  { key: 'customers', href: '/customers', icon: Users, label: 'Clientes' },
  { key: 'payments', href: '/payments', icon: CreditCard, label: 'Pagos' },
];

export function MobileBottomNav({ locale = 'es', onMenuClick }: MobileNavProps) {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 lg:hidden safe-bottom">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const href = `/${locale}${item.href}`;
          const isActive = pathname === href || pathname.startsWith(`${href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.key}
              href={href}
              className={cn(
                'flex flex-col items-center justify-center flex-1 h-full px-2 transition-colors touch-target',
                isActive
                  ? 'text-primary-600'
                  : 'text-gray-500 active:text-gray-700'
              )}
            >
              <Icon className={cn('w-5 h-5', isActive && 'text-primary-600')} />
              <span className={cn(
                'text-xs mt-1',
                isActive ? 'font-medium' : 'font-normal'
              )}>
                {item.label}
              </span>
            </Link>
          );
        })}

        <button
          onClick={onMenuClick}
          className="flex flex-col items-center justify-center flex-1 h-full px-2 text-gray-500 active:text-gray-700 touch-target"
        >
          <Menu className="w-5 h-5" />
          <span className="text-xs mt-1">Menu</span>
        </button>
      </div>
    </nav>
  );
}

export function MobileNavSpacer() {
  return <div className="h-16 lg:hidden" />;
}
