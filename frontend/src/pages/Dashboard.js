import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Users, Building2, Calendar, TrendingUp, MessageSquare, Flame, Thermometer } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

  const fetchStats = async () => {
    try {
      const { data } = await axios.get(`${API}/dashboard`, { withCredentials: true });
      setStats(data);
    } catch (e) {
      console.error('Error fetching stats:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    if (lastMessage) {
      fetchStats();
    }
  }, [lastMessage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-slate-400">{t('loading')}</div>
      </div>
    );
  }

  const statCards = [
    {
      title: t('totalClients'),
      value: stats?.total_clients || 0,
      icon: Users,
      color: 'text-[#1E3A5F]',
      bg: 'bg-blue-50'
    },
    {
      title: t('availableApts'),
      value: stats?.logements_disponibles || stats?.appartements_disponibles || 0,
      icon: Building2,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50'
    },
    {
      title: t('reservedApts'),
      value: stats?.logements_reserves || stats?.appartements_reserves || 0,
      icon: Calendar,
      color: 'text-amber-600',
      bg: 'bg-amber-50'
    },
    {
      title: t('soldApts'),
      value: stats?.logements_vendus || stats?.appartements_vendus || 0,
      icon: TrendingUp,
      color: 'text-slate-600',
      bg: 'bg-slate-100'
    },
    {
      title: t('hotLeads'),
      value: stats?.clients_par_temperature?.chaud || 0,
      icon: Flame,
      color: 'text-[#C41E3A]',
      bg: 'bg-red-50'
    },
    {
      title: t('whatsappLeads'),
      value: stats?.whatsapp_leads || 0,
      icon: MessageSquare,
      color: 'text-green-600',
      bg: 'bg-green-50'
    }
  ];

  const clientStatuses = [
    { key: 'nouveau', label: t('new'), color: 'bg-blue-100 text-blue-800 border-blue-200' },
    { key: 'intéressé', label: t('interested'), color: 'bg-violet-100 text-violet-800 border-violet-200' },
    { key: 'visite', label: t('visit'), color: 'bg-cyan-100 text-cyan-800 border-cyan-200' },
    { key: 'réservé', label: t('reserved'), color: 'bg-amber-100 text-amber-800 border-amber-200' },
    { key: 'vendu', label: t('sold'), color: 'bg-slate-200 text-slate-700 border-slate-300' }
  ];

  const temperatures = [
    { key: 'chaud', label: t('hot'), color: 'bg-red-100 text-red-800 border-red-200', icon: '🔥' },
    { key: 'tiède', label: t('warm'), color: 'bg-amber-100 text-amber-800 border-amber-200', icon: '🌡️' },
    { key: 'froid', label: t('cold'), color: 'bg-slate-100 text-slate-700 border-slate-200', icon: '❄️' }
  ];

  return (
    <div className="space-y-8 fade-in" data-testid="dashboard">
      <div>
        <h1 className="text-3xl md:text-4xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
          {t('dashboard')}
        </h1>
        <p className="text-slate-500 mt-1">{t('overview')}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 stagger-fade-in">
        {statCards.map((stat) => (
          <Card key={stat.title} className="card-luxury" data-testid={`stat-${stat.title.toLowerCase().replace(/\s/g, '-')}`}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{stat.title}</p>
                  <p className="text-3xl font-light text-[#0F1D30] mt-1">{stat.value}</p>
                </div>
                <div className={`h-12 w-12 rounded ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Blocs EDIMCO */}
      <Card className="card-luxury" data-testid="blocs-edimco">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            EDIMCO - Blocs A-H
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].map(bloc => {
              const bs = stats?.blocs_stats?.[bloc] || {};
              const total = bs.total || 0;
              const dispo = bs.disponible || 0;
              const reserve = bs.reserve || 0;
              const vendu = bs.vendu || 0;
              const pct = total > 0 ? Math.round(((reserve + vendu) / total) * 100) : 0;
              return (
                <div key={bloc} className="rounded-lg border border-slate-200 p-3 text-center hover:shadow-md transition-shadow">
                  <div className="text-lg font-bold text-[#1E3A5F] font-['Outfit']">Bloc {bloc}</div>
                  <div className="text-2xl font-light text-slate-800 mt-1">{total}</div>
                  <div className="text-xs text-slate-500 mb-2">logements</div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 mb-2">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-emerald-400 to-[#1E3A5F]"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="flex justify-center gap-2 text-xs">
                    <span className="text-emerald-600">{dispo}</span>
                    <span className="text-amber-600">{reserve}</span>
                    <span className="text-slate-500">{vendu}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clients par statut */}
        <Card className="card-luxury" data-testid="clients-by-status">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit']">{t('clientsByStatus')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {clientStatuses.map((status) => (
                <div key={status.key} className="flex items-center justify-between p-3 rounded bg-slate-50">
                  <Badge className={`${status.color} border`}>{status.label}</Badge>
                  <span className="text-xl font-light text-slate-900">
                    {stats?.clients_par_statut?.[status.key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Température des leads */}
        <Card className="card-luxury" data-testid="clients-by-temperature">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
              <Thermometer className="h-5 w-5" />
              {t('temperature')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {temperatures.map((temp) => (
                <div key={temp.key} className="flex items-center justify-between p-3 rounded bg-slate-50">
                  <div className="flex items-center gap-2">
                    <span>{temp.icon}</span>
                    <Badge className={`${temp.color} border`}>{temp.label}</Badge>
                  </div>
                  <span className="text-xl font-light text-slate-900">
                    {stats?.clients_par_temperature?.[temp.key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Derniers clients */}
        <Card className="card-luxury" data-testid="recent-clients">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit']">{t('recentClients')}</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_clients?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_clients.map((client) => (
                  <div key={client.id} className="flex items-center justify-between p-3 rounded bg-slate-50">
                    <div>
                      <p className="font-medium text-slate-900">{client.nom}</p>
                      <div className="flex items-center gap-2 mt-1">
                        {client.source === 'whatsapp' && (
                          <MessageSquare className="h-3 w-3 text-green-500" />
                        )}
                        <p className="text-xs text-slate-500">
                          {new Date(client.created_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge className={
                        client.temperature === 'chaud' ? 'bg-red-100 text-red-800 border border-red-200' :
                        client.temperature === 'tiède' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                        'bg-slate-100 text-slate-700 border border-slate-200'
                      }>
                        {client.temperature === 'chaud' ? t('hot') : 
                         client.temperature === 'tiède' ? t('warm') : t('cold')}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">{t('noClients')}</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* WhatsApp AI Status */}
      <Card className="card-luxury border-s-4 border-s-green-500" data-testid="whatsapp-status">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded bg-green-50 flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-green-500" />
            </div>
            <div>
              <p className="font-medium text-slate-900">{t('whatsapp')} - GPT-5.2</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm text-slate-600">{t('aiActive')}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
