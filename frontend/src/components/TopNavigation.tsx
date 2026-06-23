import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';

interface NavItem {
  label: string;
  href: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Upload', href: '/upload' },
  { label: 'Validation', href: '/validation' },
  { label: 'Schema Validation', href: '/schema-validation' },
  { label: 'Profiling', href: '/profiling-dashboard' },
  { label: 'Pipelines', href: '/pipelines' },
  { label: 'Logs', href: '/logs' },
  { label: 'Data Sources', href: '/data-sources' },
  { label: 'Metrics', href: '/metrics' },
  { label: 'Alerts', href: '/alerts' },
];

export default function TopNavigation() {
  const router = useRouter();
  const { userEmail, userRole, logout, isAuthenticated } = useAuth();

  const isActive = (href: string): boolean => {
    return router.pathname === href;
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">DO</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">
                Data Observability
              </span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  px-4 py-2 rounded-md text-sm font-medium transition-colors
                  ${
                    isActive(item.href)
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* User Actions */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && (
              <>
                {/* User Info */}
                <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 rounded-md">
                  <div className="flex flex-col">
                    <span className="text-xs text-gray-600">{userEmail}</span>
                    <span className="text-xs font-semibold text-blue-600 uppercase">
                      {userRole}
                    </span>
                  </div>
                </div>

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
                  aria-label="Logout"
                >
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
