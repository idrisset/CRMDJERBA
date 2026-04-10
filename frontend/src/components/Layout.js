import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  LayoutDashboard, 
  Users, 
  Building2, 
  MessageSquare, 
  Settings, 
  LogOut,
  Wifi,
  WifiOff,
  User,
  Globe,
  Database,
  Shield,
  Trash2,
  ShieldCheck,
  Copy
} from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

// Logo Component - Using original uploaded image with dark blue background
const Logo = () => (
  <img 
    src="https://customer-assets.emergentagent.com/job_property-hub-612/artifacts/wry3uaf5_IMG_1081.jpeg" 
    alt="DJERBA CONSTRUCTION" 
    className="h-20 w-auto object-contain"
  />
);

export function Layout({ children }) {
  const { user, logout } = useAuth();
  const { isConnected } = useWebSocket();
  const { t, language, setLanguage } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/', icon: LayoutDashboard, label: t('dashboard') },
    { to: '/clients', icon: Users, label: t('clients') },
    { to: '/appartements', icon: Building2, label: t('apartments') },
    { to: '/prospects', icon: Database, label: t('prospects') },
    { to: '/doublons', icon: Copy, label: t('duplicates') },
    { to: '/audit-log', icon: Shield, label: t('auditLog') },
    { to: '/corbeille', icon: Trash2, label: t('trash') },
    { to: '/whatsapp', icon: MessageSquare, label: t('whatsapp') },
  ];

  // Admin-only nav items
  const perms = user?.permissions;
  if (perms?.can_manage_users || user?.role === 'super_admin' || user?.role === 'admin') {
    navItems.push({ to: '/admin', icon: ShieldCheck, label: t('administration') });
  }
  if (perms?.level >= 2 || user?.role === 'super_admin' || user?.role === 'admin') {
    navItems.push({ to: '/parametres', icon: Settings, label: t('settings') });
  }

  const languages = [
    { code: 'fr', label: 'Français', flag: '🇫🇷' },
    { code: 'ar', label: 'العربية', flag: '🇩🇿' },
    { code: 'en', label: 'English', flag: '🇬🇧' },
  ];

  return (
    <div className="flex min-h-screen bg-[#F8F9FA]">
      {/* Sidebar */}
      <aside className="sidebar-luxury" data-testid="sidebar">
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center justify-center">
            <Logo />
          </div>
        </div>

        <nav className="flex-1 py-6">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'active' : ''}`
              }
              data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User info */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-full bg-[#C41E3A] flex items-center justify-center">
              <User className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.name || user?.email}</p>
              <p className="text-xs text-slate-400 capitalize">{
                user?.role === 'super_admin' || user?.role === 'admin' ? t('superAdmin') :
                user?.role === 'admin_limited' ? t('adminLimited') :
                t('userRole')
              }</p>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs">
              {isConnected ? (
                <>
                  <Wifi className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="text-emerald-400">{t('online')}</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-3.5 w-3.5 text-red-400" />
                  <span className="text-red-400">{t('offline')}</span>
                </>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-slate-400 hover:text-white hover:bg-white/10"
              data-testid="logout-btn"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content-luxury">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-end gap-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2" data-testid="language-switcher">
                <Globe className="h-4 w-4" />
                <span>{languages.find(l => l.code === language)?.flag}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {languages.map((lang) => (
                <DropdownMenuItem 
                  key={lang.code} 
                  onClick={() => setLanguage(lang.code)}
                  className={language === lang.code ? 'bg-slate-100' : ''}
                  data-testid={`lang-${lang.code}`}
                >
                  <span className="me-2">{lang.flag}</span>
                  {lang.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
