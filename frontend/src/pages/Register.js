import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, formatApiErrorDetail } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Loader2 } from 'lucide-react';

// Logo SVG
const Logo = () => (
  <svg viewBox="0 0 60 60" className="h-16 w-16" fill="none">
    <path d="M30 8L8 24V52H24V38H36V52H52V24L30 8Z" fill="#C41E3A" />
    <path d="M30 8L8 24H18L30 15L42 24H52L30 8Z" fill="#1E3A5F" />
    <circle cx="30" cy="30" r="4" fill="white" />
    <path d="M30 34V48" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
    <path d="M26 44H34" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
  </svg>
);

export function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(email, password, name);
      navigate('/');
    } catch (e) {
      setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center px-4 relative"
      style={{
        background: 'linear-gradient(135deg, #1E3A5F 0%, #122339 100%)'
      }}
    >
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 start-20 w-64 h-64 border border-white/20 rounded-full"></div>
        <div className="absolute bottom-20 end-20 w-96 h-96 border border-white/20 rounded-full"></div>
      </div>

      <Card className="w-full max-w-md shadow-2xl border-0 bg-white/95 backdrop-blur relative z-10">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4">
            <Logo />
          </div>
          <CardTitle className="text-2xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            DJERBA CONSTRUCTION
          </CardTitle>
          <CardDescription className="text-slate-500">
            {t('createAccount')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded bg-red-50 text-red-600 text-sm border border-red-200" data-testid="register-error">
                {error}
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-600">{t('name')}</Label>
              <Input
                id="name"
                type="text"
                placeholder="Jean Dupont"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="border-slate-200 focus:border-[#1E3A5F] focus:ring-[#1E3A5F]"
                data-testid="register-name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-600">{t('email')}</Label>
              <Input
                id="email"
                type="email"
                placeholder="votre@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="border-slate-200 focus:border-[#1E3A5F] focus:ring-[#1E3A5F]"
                data-testid="register-email"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-600">{t('password')}</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="border-slate-200 focus:border-[#1E3A5F] focus:ring-[#1E3A5F]"
                data-testid="register-password"
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-[#1E3A5F] hover:bg-[#2A4D7C] text-white"
              disabled={loading}
              data-testid="register-submit"
            >
              {loading ? (
                <>
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                t('signUp')
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-600">
            {t('hasAccount')}{' '}
            <Link to="/login" className="text-[#C41E3A] hover:underline font-medium" data-testid="login-link">
              {t('signIn')}
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
