'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useAuthStore } from '@/stores/auth';
import {
  LayoutDashboard,
  Package,
  Users,
  FileText,
  Receipt,
  CreditCard,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { MobileBottomNav, MobileNavSpacer } from '@/components/ui/mobile-nav';

interface DashboardLayoutProps {
  children: ReactNode;
}

const navItems = [
  { key: 'dashboard', href: '/dashboard', icon: LayoutDashboard },
  { key: 'units', href: '/units', icon: Package },
  { key: 'customers', href: '/customers', icon: Users },
  { key: 'contracts', href: '/contracts', icon: FileText },
  { key: 'invoices', href: '/invoices', icon: Receipt },
  { key: 'payments', href: '/payments', icon: CreditCard },
  { key: 'reports', href: '/reports', icon: BarChart3 },
  { key: 'settings', href: '/settings', icon: Settings },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const t = useTranslations('nav');
  const router = useRouter();
  const pathname = usePathname();
  const { user, tenant, isAuthenticated, isLoading, loadUser, loadTenant, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    loadUser();
    loadTenant();
  }, [loadUser, loadTenant]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/es/login');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleLogout = () => {
    logout();
    router.push('/es/login');
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600" />
      </div>
    );
  }

  const locale = pathname.split('/')[1] || 'es';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
            <Link href={`/${locale}/dashboard`} className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Package className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-lg text-gray-900">Bodega CR</span>
            </Link>
            <button onClick={() => setSidebarOpen(false)} className="lg:hidden">
              <X className="w-6 h-6 text-gray-500" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const href = `/${locale}${item.href}`;
              const isActive = pathname === href || pathname.startsWith(`${href}/`);
              const Icon = item.icon;

              return (
                <Link
                  key={item.key}
                  href={href}
                  className={cn(
                    'sidebar-link',
                    isActive ? 'sidebar-link-active' : 'sidebar-link-inactive'
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  {t(item.key)}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-primary-600 font-medium">
                  {user?.first_name?.[0]}{user?.last_name?.[0]}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500 truncate">{tenant?.name}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="sidebar-link sidebar-link-inactive w-full text-danger-600 hover:bg-danger-50 hover:text-danger-700"
            >
              <LogOut className="w-5 h-5" />
              {t('logout') || 'Cerrar Sesion'}
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <header className="sticky top-0 z-30 bg-white border-b border-gray-200 lg:hidden">
          <div className="flex items-center justify-between h-16 px-4">
            <button onClick={() => setSidebarOpen(true)}>
              <Menu className="w-6 h-6 text-gray-600" />
            </button>
            <span className="font-bold text-lg text-gray-900">Bodega CR</span>
            <div className="w-6" /> {/* Spacer */}
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8 pb-20 lg:pb-8">
          {children}
        </main>

        {/* Mobile bottom spacer */}
        <MobileNavSpacer />
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav locale={locale} onMenuClick={() => setSidebarOpen(true)} />
    </div>
  );
}
