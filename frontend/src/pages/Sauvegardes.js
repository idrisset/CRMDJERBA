import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import {
  HardDrive, Download, RotateCcw, Trash2, Plus, Check, X,
  Clock, Shield, AlertTriangle, Loader2, Database, Calendar
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

export function Sauvegardes() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [backups, setBackups] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoreTarget, setRestoreTarget] = useState(null);
  const [restoring, setRestoring] = useState(false);

  const isSuperAdmin = user?.permissions?.level >= 3 || user?.role === 'super_admin' || user?.role === 'admin';

  const fetchData = useCallback(async () => {
    try {
      const [backupsRes, statsRes] = await Promise.all([
        axios.get(`${API}/backups`),
        axios.get(`${API}/backups/stats`),
      ]);
      setBackups(backupsRes.data || []);
      setStats(statsRes.data || null);
    } catch (e) {
      console.error('Backup fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const { data } = await axios.post(`${API}/backups`);
      toast.success(`Sauvegarde créée avec succès (${data.size_mb} MB)`);
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setCreating(false);
    }
  };

  const handleRestore = async () => {
    if (!restoreTarget) return;
    setRestoring(true);
    try {
      const { data } = await axios.post(`${API}/backups/${restoreTarget.backup_id}/restore`);
      toast.success('Restauration réussie ! Une sauvegarde de sécurité a été créée automatiquement.');
      setRestoreTarget(null);
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de la restauration');
    } finally {
      setRestoring(false);
    }
  };

  const handleDelete = async (backupId) => {
    if (!window.confirm('Supprimer cette sauvegarde ?')) return;
    try {
      await axios.delete(`${API}/backups/${backupId}`);
      toast.success('Sauvegarde supprimée');
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur');
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  const getTypeBadge = (type) => {
    const types = {
      manual: { label: 'Manuel', class: 'bg-blue-100 text-blue-800 border-blue-200' },
      auto_6h: { label: 'Auto 6h', class: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
      auto_daily: { label: 'Quotidien', class: 'bg-violet-100 text-violet-800 border-violet-200' },
      pre_restore: { label: 'Pré-restauration', class: 'bg-amber-100 text-amber-800 border-amber-200' },
    };
    const t = types[type] || { label: type, class: 'bg-slate-100 text-slate-700 border-slate-200' };
    return <Badge className={`${t.class} border text-xs`}>{t.label}</Badge>;
  };

  const getStatusBadge = (status) => {
    if (status === 'success') return <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs"><Check className="h-3 w-3 me-1 inline" />Réussi</Badge>;
    if (status === 'failed') return <Badge className="bg-red-100 text-red-800 border border-red-200 text-xs"><X className="h-3 w-3 me-1 inline" />Échoué</Badge>;
    return <Badge className="bg-amber-100 text-amber-800 border border-amber-200 text-xs"><Loader2 className="h-3 w-3 me-1 inline animate-spin" />En cours</Badge>;
  };

  if (!isSuperAdmin) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="backup-forbidden">
        <div className="text-center">
          <Shield className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Accès réservé au Super Administrateur</p>
        </div>
      </div>
    );
  }

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-6 fade-in" data-testid="backups-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            Sauvegardes & Restauration
          </h1>
          <p className="text-slate-500 mt-1">Protection des données du CRM</p>
        </div>
        <Button
          onClick={handleCreate}
          disabled={creating}
          className="bg-[#1E3A5F] hover:bg-[#2A4D7C]"
          data-testid="create-backup-btn"
        >
          {creating ? <Loader2 className="h-4 w-4 animate-spin me-2" /> : <Plus className="h-4 w-4 me-2" />}
          {creating ? 'Sauvegarde en cours...' : 'Créer une sauvegarde'}
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="card-luxury">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-blue-50 flex items-center justify-center">
                <Database className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Total</p>
                <p className="text-2xl font-light text-[#0F1D30]">{stats?.total || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="card-luxury">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-emerald-50 flex items-center justify-center">
                <Check className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Réussies</p>
                <p className="text-2xl font-light text-[#0F1D30]">{stats?.successful || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="card-luxury">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-amber-50 flex items-center justify-center">
                <HardDrive className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Taille</p>
                <p className="text-2xl font-light text-[#0F1D30]">{stats?.total_size_mb || 0} MB</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="card-luxury">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded bg-violet-50 flex items-center justify-center">
                <Calendar className="h-5 w-5 text-violet-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Dernière</p>
                <p className="text-sm font-medium text-[#0F1D30]">
                  {stats?.last_backup ? formatDate(stats.last_backup.created_at) : 'Aucune'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Scheduler Info */}
      <Card className="card-luxury border-s-4 border-s-emerald-500">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 rounded bg-emerald-50 flex items-center justify-center">
              <Clock className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="font-medium text-slate-900">Sauvegardes automatiques actives</p>
              <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  Toutes les 6 heures
                </span>
                <span className="flex items-center gap-1">
                  <div className="h-2 w-2 rounded-full bg-violet-500 animate-pulse" />
                  Quotidien à 02h00
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Conservation : 7 jours (quotidien) + 4 semaines + 3 mois
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Backup List */}
      <Card className="card-luxury" data-testid="backups-list">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Journal des sauvegardes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {backups.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <HardDrive className="h-14 w-14 mx-auto mb-4 text-slate-200" />
              <p className="text-lg">Aucune sauvegarde</p>
              <p className="text-sm mt-1">Créez votre première sauvegarde pour protéger vos données</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#1E3A5F]">
                    <TableHead className="text-white text-xs">Date & Heure</TableHead>
                    <TableHead className="text-white text-xs">Type</TableHead>
                    <TableHead className="text-white text-xs">Statut</TableHead>
                    <TableHead className="text-white text-xs">Taille</TableHead>
                    <TableHead className="text-white text-xs">Créé par</TableHead>
                    <TableHead className="text-white text-xs w-[130px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backups.map(b => (
                    <TableRow key={b.backup_id} className="hover:bg-slate-50" data-testid={`backup-row-${b.backup_id}`}>
                      <TableCell>
                        <div className="text-sm font-medium">{formatDate(b.created_at)}</div>
                        <div className="text-xs text-slate-400 font-mono">{b.backup_id?.split('_').slice(-2).join('_')}</div>
                      </TableCell>
                      <TableCell>{getTypeBadge(b.type)}</TableCell>
                      <TableCell>{getStatusBadge(b.status)}</TableCell>
                      <TableCell>
                        <span className="text-sm font-medium">{b.size_mb || 0} MB</span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-slate-600">{b.triggered_by || '-'}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {b.status === 'success' && b.exists !== false && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50"
                              onClick={() => setRestoreTarget(b)}
                              data-testid={`restore-${b.backup_id}`}
                            >
                              <RotateCcw className="h-3 w-3 me-1" />
                              Restaurer
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-red-400 hover:text-red-600 hover:bg-red-50"
                            onClick={() => handleDelete(b.backup_id)}
                            data-testid={`delete-backup-${b.backup_id}`}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Restore Confirmation Dialog */}
      <Dialog open={!!restoreTarget} onOpenChange={() => setRestoreTarget(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F] flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Confirmer la restauration
            </DialogTitle>
            <DialogDescription>
              Cette action va remplacer toutes les données actuelles par celles de la sauvegarde sélectionnée.
            </DialogDescription>
          </DialogHeader>

          {restoreTarget && (
            <div className="space-y-3">
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
                <p className="text-sm font-medium text-amber-900">Sauvegarde sélectionnée :</p>
                <p className="text-sm text-amber-800 mt-1">{formatDate(restoreTarget.created_at)}</p>
                <p className="text-xs text-amber-600 mt-1">{restoreTarget.backup_id}</p>
                <p className="text-xs text-amber-600">{restoreTarget.size_mb} MB - {restoreTarget.type}</p>
              </div>
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
                <p className="text-xs text-blue-800">
                  <Shield className="h-3 w-3 inline me-1" />
                  Une sauvegarde de sécurité sera créée automatiquement avant la restauration.
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setRestoreTarget(null)} disabled={restoring}>
              Annuler
            </Button>
            <Button
              className="bg-amber-600 hover:bg-amber-700"
              onClick={handleRestore}
              disabled={restoring}
              data-testid="confirm-restore-btn"
            >
              {restoring ? <Loader2 className="h-4 w-4 animate-spin me-2" /> : <RotateCcw className="h-4 w-4 me-2" />}
              {restoring ? 'Restauration...' : 'Confirmer la restauration'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
