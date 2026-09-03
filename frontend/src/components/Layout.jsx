import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import useAuthStore from '../store/authStore';
import { 
  LayoutDashboard, FileCheck, Users, BookOpen, FileText, LogOut, 
  Menu, X, ChevronDown, CheckCircle2, AlertTriangle, Info
} from 'lucide-react';

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Панель управления', icon: LayoutDashboard },
    { path: '/checks', label: 'Проверки', icon: FileCheck },
    { path: '/ntd', label: 'База НТД', icon: BookOpen },
    { path: '/reports', label: 'Отчеты', icon: FileText },
    { path: '/users', label: 'Пользователи', icon: Users, adminOnly: true },
  ];

  const filteredNavItems = user?.role === 'admin' 
    ? navItems 
    : navItems.filter(item => !item.adminOnly);

  return (
    <div className="min-h-screen bg-dark-900 flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-dark-800 border-r border-dark-700 transition-all duration-300 flex flex-col`}>
        <div className="p-4 border-b border-dark-700 flex items-center justify-between">
          {sidebarOpen && (
            <h1 className="text-lg font-bold text-white truncate">Инженерные системы</h1>
          )}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 hover:bg-dark-700 rounded-lg text-dark-400 hover:text-white">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-dark-400 hover:bg-dark-700 hover:text-white'
                }`}
              >
                <Icon size={20} />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-dark-700">
          <div className={`flex items-center gap-3 ${sidebarOpen ? 'justify-between' : 'justify-center'}`}>
            {sidebarOpen && (
              <div className="text-sm">
                <p className="text-white font-medium">{user?.login}</p>
                <p className="text-dark-500 text-xs">{user?.role === 'admin' ? 'Администратор' : 'Инженер'}</p>
              </div>
            )}
            <button onClick={handleLogout} className="p-2 hover:bg-red-900/50 rounded-lg text-dark-400 hover:text-red-400">
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <header className="bg-dark-800 border-b border-dark-700 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">
            {filteredNavItems.find(item => item.path === location.pathname)?.label || 'Панель управления'}
          </h2>
          <div className="flex items-center gap-4">
            <span className="text-sm text-dark-400">Режим работы: Локальный</span>
          </div>
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default Layout;
