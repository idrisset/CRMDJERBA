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
  Globe
} from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

// Logo SVG Component
const Logo = () => (
  <svg viewBox="0 0 40 40" className="h-8 w-8" fill="none">
    <path d="M20 4L4 16V36H16V26H24V36H36V16L20 4Z" fill="#C41E3A" />
    <path d="M20 4L4 16H12L20 10L28 16H36L20 4Z" fill="#1E3A5F" />
    <circle cx="20" cy="20" r="3" fill="white" />
    <path d="M20 23V32" stroke="white" strokeWidth="2" strokeLinecap="round" />
    <path d="M17 29H23" stroke="white" strokeWidth="2" strokeLinecap="round" />
  </svg>
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
    { to: '/whatsapp', icon: MessageSquare, label: t('whatsapp') },
  ];

  if (user?.role === 'admin') {
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
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <Logo />
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight font-['Outfit']">
                DJERBA
              </h1>
              <p className="text-xs text-slate-400 uppercase tracking-widest">Construction</p>
            </div>
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
              <p className="text-xs text-slate-400 capitalize">{user?.role === 'admin' ? t('admin') : t('commercial')}</p>
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
