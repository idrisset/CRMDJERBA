import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Users, Building2, Calendar, TrendingUp, MessageSquare, Clock, Database, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

export function Dashboard() {
  const [stats, setStats] = useState(null);
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

  const fetchStats = async () => {
    try {
      const [statsRes, reservRes] = await Promise.all([
        axios.get(`${API}/dashboard`),
        axios.get(`${API}/reservations`),
      ]);
      setStats(statsRes.data);
      setReservations(reservRes.data || []);
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

  const totalApparts = stats?.total_appartements || 0;

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const { data } = await axios.post(`${API}/admin/seed`);
      toast.success(data.message);
      fetchStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur de seed');
    } finally {
      setSeeding(false);
    }
  };

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

  return (
    <div className="space-y-6 fade-in" data-testid="dashboard">
      <div>
        <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
          EDIMCO - {t('dashboard')}
        </h1>
        <p className="text-slate-500 mt-1">{t('overview')}</p>
      </div>

      {/* Seed Button if empty */}
      {totalApparts === 0 && !loading && (
        <Card className="border-amber-200 bg-amber-50" data-testid="seed-banner">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-amber-800">Base de données vide</p>
                <p className="text-sm text-amber-600 mt-1">Cliquez pour charger les 296 lots EDIMCO</p>
              </div>
              <Button onClick={handleSeed} disabled={seeding} className="bg-[#C41E3A] hover:bg-[#9A152C]" data-testid="seed-btn">
                {seeding ? <Loader2 className="h-4 w-4 animate-spin me-2" /> : <Database className="h-4 w-4 me-2" />}
                {seeding ? 'Chargement...' : 'Initialiser EDIMCO'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 stagger-fade-in">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                    <Badge className={
                      client.statut === 'réservé' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      client.statut === 'vendu' ? 'bg-slate-200 text-slate-700 border border-slate-300' :
                      client.statut === 'intéressé' ? 'bg-violet-100 text-violet-800 border border-violet-200' :
                      'bg-blue-100 text-blue-800 border border-blue-200'
                    }>
                      {client.statut}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">{t('noClients')}</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Historique des réservations */}
      {reservations.length > 0 && (
        <Card className="card-luxury" data-testid="recent-reservations">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Historique des réservations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {reservations.slice(0, 10).map((r) => (
                <div key={r.id} className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-slate-100">
                  <div className="flex items-center gap-3">
                    <Badge className={
                      r.action === 'réservé' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      r.action === 'vendu' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                      'bg-slate-100 text-slate-600 border border-slate-200'
                    }>
                      {r.action}
                    </Badge>
                    <div>
                      <span className="text-sm font-medium">{r.client_nom || 'Client'}</span>
                      <span className="text-xs text-slate-400 mx-2">→</span>
                      <span className="text-xs font-mono text-[#1E3A5F] font-bold">Lot {r.numero_lot}</span>
                      <span className="text-xs text-slate-500"> Bloc {r.bloc} - {r.type_appart}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-400">{r.agent}</p>
                    <p className="text-xs text-slate-400">{new Date(r.date).toLocaleDateString('fr-FR')} {new Date(r.date).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

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
