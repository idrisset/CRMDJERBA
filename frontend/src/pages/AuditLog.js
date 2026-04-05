import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import {
  Search, Loader2, Shield, LogIn, LogOut, PlusCircle, Pencil, Trash2,
  RotateCcw, AlertTriangle
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ACTION_CONFIG = {
  CREATE: { icon: PlusCircle, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
  UPDATE: { icon: Pencil, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' },
  DELETE: { icon: Trash2, color: 'text-red-600', bg: 'bg-red-50 border-red-200' },
  RESTORE: { icon: RotateCcw, color: 'text-violet-600', bg: 'bg-violet-50 border-violet-200' },
  PERMANENT_DELETE: { icon: AlertTriangle, color: 'text-red-800', bg: 'bg-red-100 border-red-300' },
  LOGIN: { icon: LogIn, color: 'text-teal-600', bg: 'bg-teal-50 border-teal-200' },
  LOGOUT: { icon: LogOut, color: 'text-slate-600', bg: 'bg-slate-50 border-slate-200' },
};

const ENTITY_LABELS = {
  client: 'Client',
  prospect: 'Prospect',
  appartement: 'Appartement',
  session: 'Session',
};

export function AuditLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [entityFilter, setEntityFilter] = useState('all');
  const { t } = useLanguage();

  const fetchLogs = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (actionFilter !== 'all') params.append('action', actionFilter);
      if (entityFilter !== 'all') params.append('entity_type', entityFilter);
      if (search) params.append('search', search);
      const { data } = await axios.get(`${API}/audit-logs?${params}`);
      setLogs(data || []);
    } catch (e) {
      console.error('Audit log fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, [actionFilter, entityFilter, search]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const formatDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const renderChanges = (log) => {
    if (!log.old_values && !log.new_values) return null;
    if (log.action === 'CREATE' && log.new_values) {
      const keys = Object.keys(log.new_values).filter(k => log.new_values[k] && !['updated_at', 'deleted_at'].includes(k));
      if (keys.length === 0) return null;
      return <span className="text-xs text-slate-400">{keys.length} champs</span>;
    }
    if (log.old_values) {
      const changes = Object.keys(log.old_values).filter(k => !['updated_at'].includes(k));
      return (
        <div className="space-y-0.5">
          {changes.slice(0, 3).map(k => (
            <div key={k} className="text-xs">
              <span className="text-slate-400">{k}:</span>{' '}
              <span className="text-red-400 line-through">{String(log.old_values[k] || '-').slice(0, 20)}</span>
              {' → '}
              <span className="text-emerald-600">{String(log.new_values?.[k] || '-').slice(0, 20)}</span>
            </div>
          ))}
          {changes.length > 3 && <span className="text-xs text-slate-400">+{changes.length - 3} autres</span>}
        </div>
      );
    }
    return null;
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-5 fade-in" data-testid="audit-log-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            <Shield className="inline h-6 w-6 me-2 mb-1" />{t('auditLog')}
          </h1>
          <p className="text-slate-500 mt-1">{logs.length} {t('actions')}</p>
        </div>
      </div>

      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder={t('searchAudit')} value={search} onChange={e => setSearch(e.target.value)} className="ps-10" data-testid="search-audit" />
        </div>
        <Select value={actionFilter} onValueChange={setActionFilter}>
          <SelectTrigger className="w-40" data-testid="filter-action"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allActions')}</SelectItem>
            <SelectItem value="CREATE">CREATE</SelectItem>
            <SelectItem value="UPDATE">UPDATE</SelectItem>
            <SelectItem value="DELETE">DELETE</SelectItem>
            <SelectItem value="RESTORE">RESTORE</SelectItem>
            <SelectItem value="PERMANENT_DELETE">PERMANENT DELETE</SelectItem>
            <SelectItem value="LOGIN">LOGIN</SelectItem>
            <SelectItem value="LOGOUT">LOGOUT</SelectItem>
          </SelectContent>
        </Select>
        <Select value={entityFilter} onValueChange={setEntityFilter}>
          <SelectTrigger className="w-40" data-testid="filter-entity"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allEntities')}</SelectItem>
            <SelectItem value="client">Client</SelectItem>
            <SelectItem value="prospect">Prospect</SelectItem>
            <SelectItem value="appartement">Appartement</SelectItem>
            <SelectItem value="session">Session</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="border-slate-200">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#1E3A5F]">
                <TableHead className="text-white text-xs font-medium w-[160px]">{t('dateTime')}</TableHead>
                <TableHead className="text-white text-xs font-medium">{t('user')}</TableHead>
                <TableHead className="text-white text-xs font-medium">{t('action')}</TableHead>
                <TableHead className="text-white text-xs font-medium">{t('entity')}</TableHead>
                <TableHead className="text-white text-xs font-medium">{t('name')}</TableHead>
                <TableHead className="text-white text-xs font-medium">{t('changes')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length > 0 ? logs.map((log, i) => {
                const cfg = ACTION_CONFIG[log.action] || ACTION_CONFIG.CREATE;
                const Icon = cfg.icon;
                return (
                  <TableRow key={i} className="hover:bg-slate-50" data-testid={`audit-row-${i}`}>
                    <TableCell className="text-xs text-slate-600 font-mono">{formatDate(log.timestamp)}</TableCell>
                    <TableCell className="text-sm font-medium">{log.user_name || '-'}</TableCell>
                    <TableCell>
                      <Badge className={`${cfg.bg} ${cfg.color} border text-xs gap-1`}>
                        <Icon className="h-3 w-3" /> {log.action}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">{ENTITY_LABELS[log.entity_type] || log.entity_type}</Badge>
                    </TableCell>
                    <TableCell className="text-sm">{log.entity_name || '-'}</TableCell>
                    <TableCell>{renderChanges(log)}</TableCell>
                  </TableRow>
                );
              }) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-10 text-slate-400">{t('noLogs')}</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
