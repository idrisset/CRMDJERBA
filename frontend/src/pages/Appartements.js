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
import { Plus, Pencil, Trash2, Building2, Loader2, Home, FileSpreadsheet, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BLOCS = ['Tous', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
const DESTINATIONS = ['Tous', 'Logement', 'Commerce', 'Service', 'Parking', 'Creche'];
const APPART_TYPES = ['F2', 'F3', 'F4', 'F4 Duplex', 'F5 Duplex', 'Commerce', 'Service', 'Parking', 'Creche'];
const ITEMS_PER_PAGE = 30;

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

  // Filters
  const [filterBloc, setFilterBloc] = useState('Tous');
  const [filterDestination, setFilterDestination] = useState('Logement');
  const [filterType, setFilterType] = useState('Tous');
  const [searchLot, setSearchLot] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const APPART_STATUSES = [
    { value: 'disponible', label: t('available'), color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
    { value: 'réservé', label: t('reserved'), color: 'bg-amber-100 text-amber-800 border-amber-200' },
    { value: 'vendu', label: t('sold'), color: 'bg-slate-200 text-slate-700 border-slate-300' },
  ];

  const [formData, setFormData] = useState({
    residence_id: '',
    type_appart: 'F2',
    prix: '',
    etage: '',
    surface_habitable: '',
    surface_utile: '',
    description: '',
    statut: 'disponible',
    client_id: '',
    bloc: '',
    numero_lot: '',
    destination: 'Logement',
  });

  const fetchData = async () => {
    try {
      const [appartsRes, residencesRes, clientsRes] = await Promise.all([
        axios.get(`${API}/appartements`, { withCredentials: true }),
        axios.get(`${API}/residences`, { withCredentials: true }),
        axios.get(`${API}/clients`, { withCredentials: true }),
      ]);
      setAppartements(appartsRes.data || []);
      setResidences(residencesRes.data || []);
      setClients(clientsRes.data || []);
    } catch (e) {
      if (e.response?.status !== 401) toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  useEffect(() => {
    if (lastMessage?.type?.includes('appartement') || lastMessage?.type?.includes('residence')) {
      fetchData();
    }
  }, [lastMessage]);

  // Filtered data
  const filtered = useMemo(() => {
    let data = [...appartements];
    if (filterBloc !== 'Tous') data = data.filter(a => a.bloc === filterBloc);
    if (filterDestination !== 'Tous') data = data.filter(a => a.destination === filterDestination);
    if (filterType !== 'Tous') data = data.filter(a => a.type_appart === filterType);
    if (searchLot) data = data.filter(a => a.numero_lot?.includes(searchLot));
    // Sort by lot number
    data.sort((a, b) => parseInt(a.numero_lot || 0) - parseInt(b.numero_lot || 0));
    return data;
  }, [appartements, filterBloc, filterDestination, filterType, searchLot]);

  // Pagination
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginatedData = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  useEffect(() => { setCurrentPage(1); }, [filterBloc, filterDestination, filterType, searchLot]);

  // Stats
  const stats = useMemo(() => {
    const logements = appartements.filter(a => a.destination === 'Logement');
    return {
      total: logements.length,
      disponible: logements.filter(a => a.statut === 'disponible').length,
      reserve: logements.filter(a => a.statut === 'réservé').length,
      vendu: logements.filter(a => a.statut === 'vendu').length,
    };
  }, [appartements]);

  // Available types based on current filter
  const availableTypes = useMemo(() => {
    let data = appartements;
    if (filterDestination !== 'Tous') data = data.filter(a => a.destination === filterDestination);
    if (filterBloc !== 'Tous') data = data.filter(a => a.bloc === filterBloc);
    const types = [...new Set(data.map(a => a.type_appart).filter(Boolean))];
    return types.sort();
  }, [appartements, filterDestination, filterBloc]);

  const resetForm = () => {
    const edimcoRes = residences.find(r => r.nom === 'EDIMCO');
    setFormData({
      residence_id: edimcoRes?.id || '',
      type_appart: 'F2', prix: '', etage: '',
      surface_habitable: '', surface_utile: '',
      description: '', statut: 'disponible', client_id: '',
      bloc: '', numero_lot: '', destination: 'Logement',
    });
    setEditingAppart(null);
  };

  const openDialog = (appart = null) => {
    if (appart) {
      setEditingAppart(appart);
      setFormData({
        residence_id: appart.residence_id || '',
        type_appart: appart.type_appart || 'F2',
        prix: appart.prix?.toString() || '',
        etage: appart.etage?.toString() || '',
        surface_habitable: appart.surface_habitable?.toString() || '',
        surface_utile: appart.surface_utile?.toString() || '',
        description: appart.description || '',
        statut: appart.statut || 'disponible',
        client_id: appart.client_id || '',
        bloc: appart.bloc || '',
        numero_lot: appart.numero_lot || '',
        destination: appart.destination || 'Logement',
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
        await axios.put(`${API}/appartements/${editingAppart.id}`, payload, { withCredentials: true });
      } else {
        await axios.post(`${API}/appartements`, payload, { withCredentials: true });
      }
      toast.success(t('success'));
      setIsDialogOpen(false);
      resetForm();
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (appartId) => {
    if (!window.confirm(t('confirm') + '?')) return;
    try {
      await axios.delete(`${API}/appartements/${appartId}`, { withCredentials: true });
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(t('error'));
    }
  };

  const handleExportExcel = () => {
    window.open(`${API}/export/appartements/excel`, '_blank');
  };

  const getStatusBadge = (statut) => {
    const status = APPART_STATUSES.find(s => s.value === statut);
    return status ? <Badge className={`${status.color} border text-xs`}>{status.label}</Badge> : <Badge>{statut}</Badge>;
  };

  const getClientName = (clientId) => {
    if (!clientId) return null;
    return clients.find(c => c.id === clientId)?.nom || null;
  };

  const formatPrice = (prix) => {
    if (!prix) return '-';
    return new Intl.NumberFormat('fr-FR').format(prix) + ' DA';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" />
      </div>
    );
  }

  return (
    <div className="space-y-5 fade-in" data-testid="appartements-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            EDIMCO - {t('apartments')}
          </h1>
          <p className="text-slate-500 mt-1">264 logements | 8 commerces | 25 services | Parking</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportExcel} data-testid="export-excel">
            <FileSpreadsheet className="h-4 w-4 me-2" />
            Excel
          </Button>
          <Button onClick={() => openDialog()} className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" data-testid="add-appart-btn">
            <Plus className="h-4 w-4 me-2" />
            {t('addApartment')}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="bg-[#1E3A5F] border-0">
          <CardContent className="pt-4 pb-3">
            <p className="text-xs text-blue-200 uppercase tracking-wide">Total Logements</p>
            <p className="text-2xl font-light text-white">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-4 pb-3">
            <p className="text-xs text-emerald-600 uppercase tracking-wide">{t('available')}</p>
            <p className="text-2xl font-light text-emerald-700">{stats.disponible}</p>
          </CardContent>
        </Card>
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4 pb-3">
            <p className="text-xs text-amber-600 uppercase tracking-wide">{t('reserved')}</p>
            <p className="text-2xl font-light text-amber-700">{stats.reserve}</p>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4 pb-3">
            <p className="text-xs text-red-600 uppercase tracking-wide">{t('sold')}</p>
            <p className="text-2xl font-light text-red-700">{stats.vendu}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="border-slate-200">
        <CardContent className="pt-4 pb-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5">
              <Filter className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-600">Filtres:</span>
            </div>

            {/* Bloc filter */}
            <div className="flex gap-1">
              {BLOCS.map(b => (
                <button
                  key={b}
                  onClick={() => setFilterBloc(b)}
                  data-testid={`filter-bloc-${b.toLowerCase()}`}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    filterBloc === b
                      ? 'bg-[#1E3A5F] text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {b === 'Tous' ? 'Tous' : `Bloc ${b}`}
                </button>
              ))}
            </div>

            {/* Destination filter */}
            <Select value={filterDestination} onValueChange={v => { setFilterDestination(v); setFilterType('Tous'); }}>
              <SelectTrigger className="w-[140px] h-8 text-xs" data-testid="filter-destination">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DESTINATIONS.map(d => (
                  <SelectItem key={d} value={d}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Type filter */}
            {availableTypes.length > 1 && (
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[130px] h-8 text-xs" data-testid="filter-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Tous">Tous types</SelectItem>
                  {availableTypes.map(t => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Search by lot */}
            <div className="relative">
              <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="N Lot..."
                value={searchLot}
                onChange={e => setSearchLot(e.target.value)}
                className="h-8 w-[100px] pl-8 text-xs"
                data-testid="search-lot"
              />
            </div>

            <span className="text-xs text-slate-400 ms-auto">{filtered.length} resultats</span>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#1E3A5F]">
                <TableHead className="text-white text-xs font-medium w-[60px]">Lot</TableHead>
                <TableHead className="text-white text-xs font-medium w-[60px]">Bloc</TableHead>
                <TableHead className="text-white text-xs font-medium">Type</TableHead>
                <TableHead className="text-white text-xs font-medium">Etage</TableHead>
                <TableHead className="text-white text-xs font-medium text-right">Surf. Hab.</TableHead>
                <TableHead className="text-white text-xs font-medium text-right">Surf. Utile</TableHead>
                <TableHead className="text-white text-xs font-medium text-right">Prix</TableHead>
                <TableHead className="text-white text-xs font-medium text-center">Statut</TableHead>
                <TableHead className="text-white text-xs font-medium">Client</TableHead>
                <TableHead className="text-white text-xs font-medium w-[80px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length > 0 ? paginatedData.map((appart) => (
                <TableRow
                  key={appart.id}
                  className="hover:bg-slate-50 transition-colors"
                  data-testid={`appart-row-${appart.numero_lot}`}
                >
                  <TableCell className="font-mono text-xs font-medium text-[#1E3A5F]">
                    {appart.numero_lot}
                  </TableCell>
                  <TableCell>
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-[#1E3A5F]/10 text-[#1E3A5F] text-xs font-bold">
                      {appart.bloc}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm font-medium">{appart.type_appart}</TableCell>
                  <TableCell className="text-xs text-slate-600">{appart.etage}</TableCell>
                  <TableCell className="text-xs text-right font-mono">{appart.surface_habitable?.toFixed(2)} m2</TableCell>
                  <TableCell className="text-xs text-right font-mono">{appart.surface_utile?.toFixed(2)} m2</TableCell>
                  <TableCell className="text-xs text-right font-medium text-[#1E3A5F]">
                    {appart.prix ? formatPrice(appart.prix) : '-'}
                  </TableCell>
                  <TableCell className="text-center">{getStatusBadge(appart.statut)}</TableCell>
                  <TableCell className="text-xs">
                    {appart.client_id ? (
                      <span className="text-[#C41E3A] font-medium">{getClientName(appart.client_id)}</span>
                    ) : (
                      <span className="text-slate-300">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => openDialog(appart)} data-testid={`edit-appart-${appart.numero_lot}`}>
                        <Pencil className="h-3 w-3 text-slate-500" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => handleDelete(appart.id)} data-testid={`delete-appart-${appart.numero_lot}`}>
                        <Trash2 className="h-3 w-3 text-red-400" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )) : (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-12 text-slate-400">
                    <Building2 className="h-10 w-10 mx-auto mb-2 text-slate-300" />
                    Aucun resultat
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50">
            <span className="text-xs text-slate-500">
              Page {currentPage}/{totalPages} ({filtered.length} lots)
            </span>
            <div className="flex gap-1">
              <Button
                variant="outline" size="sm" className="h-7"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(p => p - 1)}
                data-testid="prev-page"
              >
                <ChevronLeft className="h-3 w-3" />
              </Button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let page;
                if (totalPages <= 5) page = i + 1;
                else if (currentPage <= 3) page = i + 1;
                else if (currentPage >= totalPages - 2) page = totalPages - 4 + i;
                else page = currentPage - 2 + i;
                return (
                  <Button
                    key={page} variant={currentPage === page ? 'default' : 'outline'}
                    size="sm" className={`h-7 w-7 p-0 text-xs ${currentPage === page ? 'bg-[#1E3A5F]' : ''}`}
                    onClick={() => setCurrentPage(page)}
                  >
                    {page}
                  </Button>
                );
              })}
              <Button
                variant="outline" size="sm" className="h-7"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(p => p + 1)}
                data-testid="next-page"
              >
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
              {editingAppart ? `${t('editApartment')} - Lot ${editingAppart.numero_lot}` : t('addApartment')}
            </DialogTitle>
            <DialogDescription>
              {editingAppart ? `Bloc ${editingAppart.bloc} | ${editingAppart.etage}` : 'Nouveau lot'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">N Lot</Label>
                <Input
                  value={formData.numero_lot}
                  onChange={e => setFormData({ ...formData, numero_lot: e.target.value })}
                  className="h-9" data-testid="appart-lot"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Bloc</Label>
                <Select value={formData.bloc} onValueChange={v => setFormData({ ...formData, bloc: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-bloc">
                    <SelectValue placeholder="Bloc" />
                  </SelectTrigger>
                  <SelectContent>
                    {['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'].map(b => (
                      <SelectItem key={b} value={b}>Bloc {b}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Destination</Label>
                <Select value={formData.destination} onValueChange={v => setFormData({ ...formData, destination: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-destination">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {['Logement', 'Commerce', 'Service', 'Parking', 'Creche'].map(d => (
                      <SelectItem key={d} value={d}>{d}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">{t('type')} *</Label>
                <Select value={formData.type_appart} onValueChange={v => setFormData({ ...formData, type_appart: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {APPART_TYPES.map(t => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Etage</Label>
                <Input
                  value={formData.etage}
                  onChange={e => setFormData({ ...formData, etage: e.target.value })}
                  placeholder="ex: Etage 05"
                  className="h-9" data-testid="appart-etage"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">{t('price')} (DA)</Label>
                <Input
                  type="number" value={formData.prix}
                  onChange={e => setFormData({ ...formData, prix: e.target.value })}
                  className="h-9" data-testid="appart-prix"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Surf. Hab. (m2)</Label>
                <Input
                  type="number" step="0.01" value={formData.surface_habitable}
                  onChange={e => setFormData({ ...formData, surface_habitable: e.target.value })}
                  className="h-9" data-testid="appart-sh"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Surf. Utile (m2)</Label>
                <Input
                  type="number" step="0.01" value={formData.surface_utile}
                  onChange={e => setFormData({ ...formData, surface_utile: e.target.value })}
                  className="h-9" data-testid="appart-su"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">{t('status')}</Label>
                <Select value={formData.statut} onValueChange={v => setFormData({ ...formData, statut: v })}>
                  <SelectTrigger className="h-9" data-testid="appart-statut">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {APPART_STATUSES.map(s => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {(formData.statut === 'réservé' || formData.statut === 'vendu') && (
                <div className="space-y-1.5">
                  <Label className="text-xs">Client</Label>
                  <Select value={formData.client_id} onValueChange={v => setFormData({ ...formData, client_id: v })}>
                    <SelectTrigger className="h-9" data-testid="appart-client">
                      <SelectValue placeholder={t('none')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">{t('none')}</SelectItem>
                      {clients.map(c => (
                        <SelectItem key={c.id} value={c.id}>{c.nom} - {c.telephone}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Notes</Label>
              <Textarea
                value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })}
                rows={2} className="text-sm" data-testid="appart-description"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>{t('cancel')}</Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-appart-btn">
                {saving && <Loader2 className="h-4 w-4 animate-spin me-2" />}
                {t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
