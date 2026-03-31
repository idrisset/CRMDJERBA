import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Users, Building2, Calendar, TrendingUp, MessageSquare } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { lastMessage } = useWebSocket();

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

  // Refresh on WebSocket updates
  useEffect(() => {
    if (lastMessage) {
      fetchStats();
    }
  }, [lastMessage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-slate-400">Chargement...</div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Clients',
      value: stats?.total_clients || 0,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-50'
    },
    {
      title: 'Appartements Disponibles',
      value: stats?.appartements_disponibles || 0,
      icon: Building2,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50'
    },
    {
      title: 'Appartements Réservés',
      value: stats?.appartements_reserves || 0,
      icon: Calendar,
      color: 'text-amber-600',
      bg: 'bg-amber-50'
    },
    {
      title: 'Appartements Vendus',
      value: stats?.appartements_vendus || 0,
      icon: TrendingUp,
      color: 'text-slate-600',
      bg: 'bg-slate-100'
    }
  ];

  const clientStatuses = [
    { key: 'nouveau', label: 'Nouveaux', color: 'bg-blue-100 text-blue-800' },
    { key: 'intéressé', label: 'Intéressés', color: 'bg-violet-100 text-violet-800' },
    { key: 'visite', label: 'Visite', color: 'bg-cyan-100 text-cyan-800' },
    { key: 'réservé', label: 'Réservés', color: 'bg-amber-100 text-amber-800' },
    { key: 'vendu', label: 'Vendus', color: 'bg-slate-200 text-slate-700' }
  ];

  return (
    <div className="space-y-8 fade-in" data-testid="dashboard">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-['Outfit']">
          Tableau de bord
        </h1>
        <p className="text-slate-500 mt-1">Vue d'ensemble de votre activité immobilière</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <Card key={stat.title} className="card-stat" data-testid={`stat-${stat.title.toLowerCase().replace(/\s/g, '-')}`}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">{stat.title}</p>
                  <p className="text-3xl font-bold text-slate-900 mt-1">{stat.value}</p>
                </div>
                <div className={`h-12 w-12 rounded-lg ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Clients par statut */}
        <Card data-testid="clients-by-status">
          <CardHeader>
            <CardTitle className="text-lg font-semibold font-['Outfit']">Clients par statut</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {clientStatuses.map((status) => (
                <div key={status.key} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge className={status.color}>{status.label}</Badge>
                  </div>
                  <span className="text-xl font-semibold text-slate-900">
                    {stats?.clients_par_statut?.[status.key] || 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Derniers clients */}
        <Card data-testid="recent-clients">
          <CardHeader>
            <CardTitle className="text-lg font-semibold font-['Outfit']">Derniers clients</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_clients?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_clients.map((client) => (
                  <div key={client.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                    <div>
                      <p className="font-medium text-slate-900">{client.nom}</p>
                      <p className="text-sm text-slate-500">
                        {new Date(client.created_at).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    <Badge className={
                      client.statut === 'nouveau' ? 'bg-blue-100 text-blue-800' :
                      client.statut === 'intéressé' ? 'bg-violet-100 text-violet-800' :
                      client.statut === 'visite' ? 'bg-cyan-100 text-cyan-800' :
                      client.statut === 'réservé' ? 'bg-amber-100 text-amber-800' :
                      'bg-slate-200 text-slate-700'
                    }>
                      {client.statut}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">Aucun client récent</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* WhatsApp AI Status */}
      <Card data-testid="whatsapp-status">
        <CardHeader>
          <CardTitle className="text-lg font-semibold font-['Outfit'] flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-green-500" />
            Statut IA WhatsApp
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-slate-600">Agent IA actif et prêt à répondre</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
