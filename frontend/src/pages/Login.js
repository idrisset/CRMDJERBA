import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, formatApiErrorDetail } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Loader2 } from 'lucide-react';

// Logo Component - Using original uploaded image with dark blue background
const Logo = () => (
  <img 
    src="https://customer-assets.emergentagent.com/job_property-hub-612/artifacts/wry3uaf5_IMG_1081.jpeg" 
    alt="DJERBA CONSTRUCTION" 
    className="h-28 w-auto object-contain rounded"
  />
);

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
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
      {/* Abstract pattern overlay */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-20 start-20 w-64 h-64 border border-white/20 rounded-full"></div>
        <div className="absolute bottom-20 end-20 w-96 h-96 border border-white/20 rounded-full"></div>
        <div className="absolute top-1/2 start-1/3 w-48 h-48 border border-white/20 rounded-full"></div>
      </div>

      <Card className="w-full max-w-md shadow-2xl border-0 bg-white/95 backdrop-blur relative z-10">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4">
            <Logo />
          </div>
          <CardDescription className="text-slate-500">
            {t('login')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded bg-red-50 text-red-600 text-sm border border-red-200" data-testid="login-error">
                {error}
              </div>
            )}
            
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
                data-testid="login-email"
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
                className="border-slate-200 focus:border-[#1E3A5F] focus:ring-[#1E3A5F]"
                data-testid="login-password"
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-[#1E3A5F] hover:bg-[#2A4D7C] text-white"
              disabled={loading}
              data-testid="login-submit"
            >
              {loading ? (
                <>
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                t('signIn')
              )}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-slate-600">
            {t('noAccount')}{' '}
            <Link to="/register" className="text-[#C41E3A] hover:underline font-medium" data-testid="register-link">
              {t('createAccount')}
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
