import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import {
  Trash2, RotateCcw, Loader2, AlertTriangle, User, Home, Users
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

const ENTITY_CONFIG = {
  client: { icon: User, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200', label: 'Client' },
  prospect: { icon: Users, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200', label: 'Prospect' },
  appartement: { icon: Home, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200', label: 'Appartement' },
};

export function Corbeille() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('all');
  const [restoring, setRestoring] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

  const fetchTrash = async () => {
    try {
      const { data } = await axios.get(`${API}/trash`);
      setItems(data || []);
    } catch (e) {
      console.error('Trash fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTrash(); }, []);
  useEffect(() => {
    if (lastMessage?.type?.includes('restored') || lastMessage?.type?.includes('deleted')) fetchTrash();
  }, [lastMessage]);

  const handleRestore = async (entityType, id) => {
    setRestoring(id);
    try {
      await axios.post(`${API}/trash/${entityType}/${id}/restore`);
      toast.success(t('restored'));
      fetchTrash();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setRestoring(null);
    }
  };

  const handlePermanentDelete = async (entityType, id, name) => {
    if (!window.confirm(`${t('permanentDeleteConfirm')} "${name}" ?`)) return;
    setDeleting(id);
    try {
      await axios.delete(`${API}/trash/${entityType}/${id}/permanent`);
      toast.success(t('permanentDeleted'));
      fetchTrash();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  const filtered = typeFilter === 'all' ? items : items.filter(i => i.entity_type === typeFilter);

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-5 fade-in" data-testid="corbeille-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            <Trash2 className="inline h-6 w-6 me-2 mb-1" />{t('trash')}
          </h1>
          <p className="text-slate-500 mt-1">{items.length} {t('deletedItems')}</p>
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-44" data-testid="filter-trash-type"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allTypes')}</SelectItem>
            <SelectItem value="client">Clients</SelectItem>
            <SelectItem value="prospect">Prospects</SelectItem>
            <SelectItem value="appartement">Appartements</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {items.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="py-16 text-center">
            <Trash2 className="h-12 w-12 text-slate-200 mx-auto mb-4" />
            <p className="text-slate-400 text-lg">{t('trashEmpty')}</p>
            <p className="text-slate-300 text-sm mt-1">{t('trashEmptyDesc')}</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="border-slate-200">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="bg-[#1E3A5F]">
                  <TableHead className="text-white text-xs font-medium">{t('type')}</TableHead>
                  <TableHead className="text-white text-xs font-medium">{t('name')}</TableHead>
                  <TableHead className="text-white text-xs font-medium">{t('deletedBy')}</TableHead>
                  <TableHead className="text-white text-xs font-medium">{t('deletedAt')}</TableHead>
                  <TableHead className="text-white text-xs font-medium w-[140px]">{t('actions')}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(item => {
                  const cfg = ENTITY_CONFIG[item.entity_type] || ENTITY_CONFIG.client;
                  const Icon = cfg.icon;
                  return (
                    <TableRow key={`${item.entity_type}-${item.id}`} className="hover:bg-slate-50" data-testid={`trash-row-${item.id}`}>
                      <TableCell>
                        <Badge className={`${cfg.bg} ${cfg.color} border text-xs gap-1`}>
                          <Icon className="h-3 w-3" /> {cfg.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium text-sm">{item.entity_name || '-'}</span>
                        {item.entity_type === 'client' && item.data?.telephone && (
                          <span className="text-xs text-slate-400 ms-2">{item.data.telephone}</span>
                        )}
                        {item.entity_type === 'prospect' && item.data?.ville && (
                          <span className="text-xs text-slate-400 ms-2">{item.data.ville}</span>
                        )}
                      </TableCell>
                      <TableCell className="text-sm">{item.deleted_by_name || '-'}</TableCell>
                      <TableCell className="text-xs text-slate-600 font-mono">{formatDate(item.deleted_at)}</TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            variant="outline" size="sm"
                            className="h-7 text-xs gap-1 text-emerald-600 border-emerald-200 hover:bg-emerald-50"
                            onClick={() => handleRestore(item.entity_type, item.id)}
                            disabled={restoring === item.id}
                            data-testid={`restore-${item.id}`}
                          >
                            {restoring === item.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
                            {t('restore')}
                          </Button>
                          <Button
                            variant="outline" size="sm"
                            className="h-7 text-xs gap-1 text-red-600 border-red-200 hover:bg-red-50"
                            onClick={() => handlePermanentDelete(item.entity_type, item.id, item.entity_name)}
                            disabled={deleting === item.id}
                            data-testid={`permanent-delete-${item.id}`}
                          >
                            {deleting === item.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <AlertTriangle className="h-3 w-3" />}
                            {t('permanentDelete')}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
