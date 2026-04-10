import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Plus, Pencil, Trash2, Loader2, Search, ChevronLeft, ChevronRight, FileSpreadsheet } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;
const ITEMS_PER_PAGE = 25;

const TYPE_TABS = [
  { key: 'F2', label: 'F2' },
  { key: 'F3', label: 'F3' },
  { key: 'F4', label: 'F4' },
  { key: 'F4 Duplex', label: 'F4 Duplex' },
  { key: 'F5 Duplex', label: 'F5 Duplex' },
  { key: 'Commerce', label: 'Commerce' },
  { key: 'Service', label: 'Service' },
  { key: 'Parking', label: 'Parking' },
  { key: 'Creche', label: 'Crèche' },
];

const APPART_TYPES = ['F2', 'F3', 'F4', 'F4 Duplex', 'F5 Duplex', 'Commerce', 'Service', 'Parking', 'Creche'];

export function Appartements() {
  const [appartements, setAppartements] = useState([]);
  const [residences, setResidences] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingAppart, setEditingAppart] = useState(null);
  const [saving, setSaving] = useState(false);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

  const [activeTab, setActiveTab] = useState('F2');
  const [filterBloc, setFilterBloc] = useState('Tous');
  const [searchLot, setSearchLot] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const STATUSES = [
    { value: 'disponible', label: t('available'), color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
    { value: 'réservé', label: t('reserved'), color: 'bg-amber-100 text-amber-800 border-amber-200' },
    { value: 'vendu', label: t('sold'), color: 'bg-slate-200 text-slate-700 border-slate-300' },
  ];

  const [formData, setFormData] = useState({
    residence_id: '', type_appart: 'F2', prix: '', etage: '',
    surface_habitable: '', surface_utile: '', description: '',
    statut: 'disponible', client_id: '', bloc: '', numero_lot: '', destination: 'Logement',
  });

  const fetchData = async () => {
    try {
      const [a, r, c] = await Promise.all([
        axios.get(`${API}/appartements`),
        axios.get(`${API}/residences`),
        axios.get(`${API}/clients`),
      ]);
      setAppartements(a.data || []);
      setResidences(r.data || []);
      setClients(c.data || []);
    } catch (e) {
      if (e.response?.status !== 401) console.error('Fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => {
    if (lastMessage?.type?.includes('appartement') || lastMessage?.type?.includes('residence')) fetchData();
  }, [lastMessage]);

  // Count per type tab
  const tabCounts = useMemo(() => {
    const counts = {};
    TYPE_TABS.forEach(tab => {
      counts[tab.key] = appartements.filter(a => a.type_appart === tab.key).length;
    });
    return counts;
  }, [appartements]);

  // Filtered
  const filtered = useMemo(() => {
    let data = appartements.filter(a => a.type_appart === activeTab);
    if (filterBloc !== 'Tous') data = data.filter(a => a.bloc === filterBloc);
    if (searchLot) data = data.filter(a => a.numero_lot?.includes(searchLot));
    data.sort((a, b) => parseInt(a.numero_lot || 0) - parseInt(b.numero_lot || 0));
    return data;
  }, [appartements, activeTab, filterBloc, searchLot]);

  // Available blocs for this type
  const availableBlocs = useMemo(() => {
    const blocs = [...new Set(appartements.filter(a => a.type_appart === activeTab).map(a => a.bloc))];
    return blocs.sort();
  }, [appartements, activeTab]);

  // Stats for active tab
  const tabStats = useMemo(() => {
    const data = appartements.filter(a => a.type_appart === activeTab);
    return {
      total: data.length,
      disponible: data.filter(a => a.statut === 'disponible').length,
      reserve: data.filter(a => a.statut === 'réservé').length,
      vendu: data.filter(a => a.statut === 'vendu').length,
    };
  }, [appartements, activeTab]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);
  useEffect(() => { setCurrentPage(1); }, [activeTab, filterBloc, searchLot]);

  const resetForm = () => {
    const edimco = residences.find(r => r.nom === 'EDIMCO');
    setFormData({
      residence_id: edimco?.id || '', type_appart: activeTab, prix: '', etage: '',
      surface_habitable: '', surface_utile: '', description: '', statut: 'disponible',
      client_id: '', bloc: '', numero_lot: '',
      destination: ['Commerce', 'Service', 'Parking', 'Creche'].includes(activeTab) ? activeTab : 'Logement',
    });
    setEditingAppart(null);
  };

  const openDialog = (appart = null) => {
    if (appart) {
      setEditingAppart(appart);
      setFormData({
        residence_id: appart.residence_id || '', type_appart: appart.type_appart || 'F2',
        prix: appart.prix?.toString() || '', etage: appart.etage?.toString() || '',
        surface_habitable: appart.surface_habitable?.toString() || '',
        surface_utile: appart.surface_utile?.toString() || '',
        description: appart.description || '', statut: appart.statut || 'disponible',
        client_id: appart.client_id || '', bloc: appart.bloc || '',
        numero_lot: appart.numero_lot || '', destination: appart.destination || 'Logement',
      });
    } else {
      resetForm();
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = {
      ...formData,
      prix: parseFloat(formData.prix) || 0,
      surface: formData.surface_habitable ? parseFloat(formData.surface_habitable) : null,
      surface_habitable: formData.surface_habitable ? parseFloat(formData.surface_habitable) : null,
      surface_utile: formData.surface_utile ? parseFloat(formData.surface_utile) : null,
      client_id: formData.client_id && formData.client_id !== 'none' ? formData.client_id : null,
    };
    try {
      if (editingAppart) {
        await axios.put(`${API}/appartements/${editingAppart.id}`, payload);
      } else {
        await axios.post(`${API}/appartements`, payload);
      }
      toast.success(t('success'));
      setIsDialogOpen(false);
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirm') + '?')) return;
    try {
      await axios.delete(`${API}/appartements/${id}`);
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(t('error'));
    }
  };

  const formatPrice = (p) => p ? new Intl.NumberFormat('fr-FR').format(p) + ' DA' : '-';

  const getStatusBadge = (s) => {
    const st = STATUSES.find(x => x.value === s);
    return st ? <Badge className={`${st.color} border text-xs`}>{st.label}</Badge> : <Badge>{s}</Badge>;
  };

  const getClientName = (id) => id ? clients.find(c => c.id === id)?.nom || '-' : '-';

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;
  }

  return (
    <div className="space-y-4 fade-in" data-testid="appartements-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
          {t('apartments')}
        </h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => window.open(`${API}/export/appartements/excel`, '_blank')} data-testid="export-excel">
            <FileSpreadsheet className="h-4 w-4 me-1" /> Excel
          </Button>
          <Button size="sm" onClick={() => openDialog()} className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" data-testid="add-appart-btn">
            <Plus className="h-4 w-4 me-1" /> {t('addApartment')}
          </Button>
        </div>
      </div>

      {/* Type Tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1" data-testid="type-tabs">
        {TYPE_TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setFilterBloc('Tous'); setSearchLot(''); }}
            data-testid={`tab-${tab.key.toLowerCase().replace(' ', '-')}`}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === tab.key
                ? 'bg-[#1E3A5F] text-white shadow-md'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
            <span className={`ms-1.5 text-xs ${activeTab === tab.key ? 'text-blue-200' : 'text-slate-400'}`}>
              {tabCounts[tab.key] || 0}
            </span>
          </button>
        ))}
      </div>

      {/* Mini stats for active type */}
      <div className="flex gap-3 flex-wrap">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-50 border border-emerald-200">
          <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
          <span className="text-xs font-medium text-emerald-700">{t('available')}: {tabStats.disponible}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-50 border border-amber-200">
          <div className="w-2 h-2 rounded-full bg-amber-500"></div>
          <span className="text-xs font-medium text-amber-700">{t('reserved')}: {tabStats.reserve}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-100 border border-slate-200">
          <div className="w-2 h-2 rounded-full bg-slate-500"></div>
          <span className="text-xs font-medium text-slate-600">{t('sold')}: {tabStats.vendu}</span>
        </div>

        {/* Bloc filter */}
        {availableBlocs.length > 1 && (
          <div className="flex items-center gap-1 ms-auto">
            {['Tous', ...availableBlocs].map(b => (
              <button
                key={b}
                onClick={() => setFilterBloc(b)}
                data-testid={`filter-bloc-${b.toLowerCase()}`}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  filterBloc === b ? 'bg-[#1E3A5F] text-white' : 'bg-white text-slate-500 border border-slate-200 hover:bg-slate-50'
                }`}
              >
                {b === 'Tous' ? 'Tous' : b}
              </button>
            ))}
          </div>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="h-3.5 w-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="N Lot"
            value={searchLot}
            onChange={e => setSearchLot(e.target.value)}
            className="h-8 w-[90px] pl-7 text-xs"
            data-testid="search-lot"
          />
        </div>
      </div>

      {/* Table */}
      <Card className="border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#1E3A5F]">
                <TableHead className="text-white text-xs font-medium w-[55px]">Lot</TableHead>
                <TableHead className="text-white text-xs font-medium w-[50px]">Bloc</TableHead>
                <TableHead className="text-white text-xs font-medium">Etage</TableHead>
                <TableHead className="text-white text-xs font-medium text-right">Surface Hab.</TableHead>
                <TableHead className="text-white text-xs font-medium text-right">Surface Utile</TableHead>
                <TableHead className="text-white text-xs font-medium text-center">Statut</TableHead>
                <TableHead className="text-white text-xs font-medium">Client</TableHead>
                <TableHead className="text-white text-xs font-medium w-[70px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length > 0 ? paginatedData.map(a => (
                <TableRow key={a.id} className="hover:bg-slate-50" data-testid={`appart-row-${a.numero_lot}`}>
                  <TableCell className="font-mono text-xs font-bold text-[#1E3A5F]">{a.numero_lot}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-[#1E3A5F]/10 text-[#1E3A5F] text-xs font-bold">{a.bloc}</span>
                  </TableCell>
                  <TableCell className="text-xs text-slate-600">{a.etage}</TableCell>
                  <TableCell className="text-xs text-right font-mono">{a.surface_habitable?.toFixed(2)} m²</TableCell>
                  <TableCell className="text-xs text-right font-mono">{a.surface_utile?.toFixed(2)} m²</TableCell>
                  <TableCell className="text-center">{getStatusBadge(a.statut)}</TableCell>
                  <TableCell className="text-xs">{a.client_id ? <span className="text-[#C41E3A] font-medium">{getClientName(a.client_id)}</span> : <span className="text-slate-300">-</span>}</TableCell>
                  <TableCell>
                    <div className="flex gap-0.5">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => openDialog(a)} data-testid={`edit-${a.numero_lot}`}>
                        <Pencil className="h-3 w-3 text-slate-500" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => handleDelete(a.id)} data-testid={`delete-${a.numero_lot}`}>
                        <Trash2 className="h-3 w-3 text-red-400" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )) : (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-10 text-slate-400 text-sm">Aucun résultat</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-slate-100 bg-slate-50">
            <span className="text-xs text-slate-500">Page {currentPage}/{totalPages}</span>
            <div className="flex gap-1">
              <Button variant="outline" size="sm" className="h-7" disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)} data-testid="prev-page">
                <ChevronLeft className="h-3 w-3" />
              </Button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pg;
                if (totalPages <= 5) pg = i + 1;
                else if (currentPage <= 3) pg = i + 1;
                else if (currentPage >= totalPages - 2) pg = totalPages - 4 + i;
                else pg = currentPage - 2 + i;
                return (
                  <Button key={pg} variant={currentPage === pg ? 'default' : 'outline'} size="sm"
                    className={`h-7 w-7 p-0 text-xs ${currentPage === pg ? 'bg-[#1E3A5F]' : ''}`}
                    onClick={() => setCurrentPage(pg)}>{pg}</Button>
                );
              })}
              <Button variant="outline" size="sm" className="h-7" disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)} data-testid="next-page">
                <ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F]">
              {editingAppart ? `Lot ${editingAppart.numero_lot} - Bloc ${editingAppart.bloc}` : t('addApartment')}
            </DialogTitle>
            <DialogDescription>{editingAppart ? editingAppart.etage : 'Nouveau lot'}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">N° Lot</Label>
                <Input value={formData.numero_lot} onChange={e => setFormData({ ...formData, numero_lot: e.target.value })} className="h-9" data-testid="appart-lot" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Bloc</Label>
                <Select value={formData.bloc} onValueChange={v => setFormData({ ...formData, bloc: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-bloc"><SelectValue placeholder="Bloc" /></SelectTrigger>
                  <SelectContent>{['A','B','C','D','E','F','G','H'].map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Etage</Label>
                <Input value={formData.etage} onChange={e => setFormData({ ...formData, etage: e.target.value })} className="h-9" data-testid="appart-etage" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('type')}</Label>
                <Select value={formData.type_appart} onValueChange={v => setFormData({ ...formData, type_appart: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-type"><SelectValue /></SelectTrigger>
                  <SelectContent>{APPART_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Surf. Hab. (m²)</Label>
                <Input type="number" step="0.01" value={formData.surface_habitable} onChange={e => setFormData({ ...formData, surface_habitable: e.target.value })} className="h-9" data-testid="appart-sh" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Surf. Utile (m²)</Label>
                <Input type="number" step="0.01" value={formData.surface_utile} onChange={e => setFormData({ ...formData, surface_utile: e.target.value })} className="h-9" data-testid="appart-su" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('status')}</Label>
                <Select value={formData.statut} onValueChange={v => setFormData({ ...formData, statut: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-statut"><SelectValue /></SelectTrigger>
                  <SelectContent>{STATUSES.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            {(formData.statut === 'réservé' || formData.statut === 'vendu') && (
              <div className="space-y-1">
                <Label className="text-xs">Client</Label>
                <Select value={formData.client_id} onValueChange={v => setFormData({ ...formData, client_id: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-client"><SelectValue placeholder={t('none')} /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">{t('none')}</SelectItem>
                    {clients.map(c => <SelectItem key={c.id} value={c.id}>{c.nom} - {c.telephone}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-1">
              <Label className="text-xs">Notes</Label>
              <Textarea value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} rows={2} className="text-sm" data-testid="appart-description" />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>{t('cancel')}</Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-appart-btn">
                {saving && <Loader2 className="h-4 w-4 animate-spin me-2" />}{t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
