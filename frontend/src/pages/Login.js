import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, formatApiErrorDetail } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Loader2, Lock } from 'lucide-react';

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
      if (e.response?.data?.detail) {
        setError(formatApiErrorDetail(e.response.data.detail));
      } else if (e.response?.status) {
        setError(`Erreur serveur (${e.response.status}). Veuillez réessayer.`);
      } else if (e.code === 'ERR_NETWORK') {
        setError('Impossible de contacter le serveur. Vérifiez votre connexion.');
      } else {
        setError(e.message || 'Une erreur est survenue. Veuillez réessayer.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center px-4 py-8"
      style={{ background: '#F5F3EF' }}
      data-testid="login-page"
    >
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg px-8 py-10 sm:px-10">
          {/* Logo */}
          <div className="flex justify-center mb-5">
            <img 
              src="https://customer-assets.emergentagent.com/job_property-hub-612/artifacts/wry3uaf5_IMG_1081.jpeg" 
              alt="DJERBA CONSTRUCTION" 
              className="h-24 w-auto object-contain"
              data-testid="login-logo"
            />
          </div>

          {/* Services tags */}
          <div className="flex items-center justify-center gap-3 mb-6 text-xs font-semibold tracking-wider uppercase" style={{ color: '#1E3A5F' }}>
            <span className="flex items-center gap-1.5">
              <span style={{ color: '#C41E3A' }}>&#9670;</span> Immobilier
            </span>
            <span className="flex items-center gap-1.5">
              <span style={{ color: '#C41E3A' }}>&#9670;</span> Construction
            </span>
            <span className="flex items-center gap-1.5">
              <span style={{ color: '#C41E3A' }}>&#9670;</span> D&eacute;co Int&eacute;rieur
            </span>
          </div>

          {/* Heading */}
          <h1 className="text-center text-2xl sm:text-3xl font-bold mb-2" style={{ color: '#1E3A5F' }}>
            Bonjour, ravi de <em className="font-normal" style={{ fontStyle: 'italic' }}>vous revoir</em>
          </h1>

          {/* Subtitle */}
          <p className="text-center text-sm text-gray-500 mb-8">
            Connectez-vous pour g&eacute;rer vos appartements, clients et r&eacute;servations en un seul endroit.
          </p>

          {/* Error */}
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm border border-red-200 mb-4" data-testid="login-error">
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-bold text-gray-800 mb-1.5">
                Adresse e-mail
              </label>
              <input
                id="email"
                type="email"
                placeholder="contact@djerbaconstruction.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-lg border-0 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]/30"
                style={{ backgroundColor: '#F5F3EF' }}
                data-testid="login-email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-bold text-gray-800 mb-1.5">
                Mot de passe
              </label>
              <input
                id="password"
                type="password"
                placeholder="Saisissez votre mot de passe"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-lg border-0 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]/30"
                style={{ backgroundColor: '#F5F3EF' }}
                data-testid="login-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-full text-white font-semibold text-sm transition-all duration-200 hover:opacity-90 disabled:opacity-60"
              style={{ backgroundColor: '#1E3A5F' }}
              data-testid="login-submit"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Chargement...
                </span>
              ) : (
                "Continuer avec l'email"
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center my-5">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="px-4 text-xs text-gray-400 uppercase tracking-wide">ou</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          {/* SSO Button */}
          <button
            type="button"
            className="w-full py-3 rounded-full border border-gray-300 text-sm font-semibold text-gray-700 flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
            onClick={() => {}}
            data-testid="login-sso-button"
          >
            <Lock className="h-4 w-4" />
            Continuer avec un SSO
          </button>

          {/* Register link */}
          <p className="text-center text-sm text-gray-500 mt-5">
            Nouveau ici ?{' '}
            <Link to="/register" className="font-semibold hover:underline" style={{ color: '#C41E3A' }} data-testid="register-link">
              Cr&eacute;er un compte
            </Link>
          </p>
        </div>

        {/* Footer quote */}
        <div className="text-center mt-8">
          <p className="text-sm italic text-gray-500">
            <span className="text-lg font-bold not-italic" style={{ color: '#C41E3A' }}>&ldquo;</span>
            {' '}L&apos;art de b&acirc;tir, depuis 2023.{' '}
            <span className="text-lg font-bold not-italic" style={{ color: '#C41E3A' }}>&rdquo;</span>
          </p>
          <p className="text-xs tracking-widest uppercase text-gray-600 mt-1 font-medium">
            &mdash; Djerba Construction
          </p>
        </div>
      </div>
    </div>
  );
}
