import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
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
import { Plus, Pencil, Trash2, Search, Loader2, FileSpreadsheet, FileText, MessageSquare, Home } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

const OBJECTIFS = ['Achat personnel', 'Investissement'];
const MODES_PAIEMENT = ['Autofinancement', 'Crédit bancaire'];
const ETAGES = ['Etage 02', 'Etage 03', 'Etage 04', 'Etage 05', 'Etage 06', 'Etage 07', 'Etage 08', 'Etage 09', 'Etage 10', 'Etage 11', 'Duplex 10-11'];
const SITUATIONS = ['Célibataire', 'Marié(e)', 'Divorcé(e)', 'Veuf/Veuve', 'En couple'];

export function Clients() {
  const [clients, setClients] = useState([]);
  const [appartements, setAppartements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [saving, setSaving] = useState(false);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

  const CLIENT_STATUSES = [
    { value: 'nouveau', label: t('new'), color: 'bg-blue-100 text-blue-800 border-blue-200' },
    { value: 'intéressé', label: t('interested'), color: 'bg-violet-100 text-violet-800 border-violet-200' },
    { value: 'visite', label: t('visit'), color: 'bg-cyan-100 text-cyan-800 border-cyan-200' },
    { value: 'réservé', label: t('reserved'), color: 'bg-amber-100 text-amber-800 border-amber-200' },
    { value: 'vendu', label: t('sold'), color: 'bg-slate-200 text-slate-700 border-slate-300' },
  ];

  const emptyForm = {
    nom: '', telephone: '', telephone2: '', email: '',
    salaire: '', budget_min: '', budget_max: '',
    objectif: '', mode_paiement: '', etage_souhaite: '',
    situation_familiale: '', notes: '', statut: 'nouveau',
    appartement_id: '',
  };

  const [formData, setFormData] = useState(emptyForm);
  const [appartTypeFilter, setAppartTypeFilter] = useState('Tous');

  const fetchData = async () => {
    try {
      const c = await axios.get(`${API}/clients`);
      setClients(c.data || []);
    } catch (e) {
      console.error('Clients fetch error:', e?.response?.status, e?.response?.data, e?.message);
    }
    try {
      const a = await axios.get(`${API}/appartements`);
      setAppartements(a.data || []);
    } catch (e) {
      console.error('Appartements fetch error:', e?.message);
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => {
    if (lastMessage?.type?.includes('client') || lastMessage?.type?.includes('appartement') || lastMessage?.type === 'new_lead') fetchData();
  }, [lastMessage]);

  const availableApparts = useMemo(() => {
    let apparts = appartements.filter(a =>
      a.destination === 'Logement' &&
      (a.statut === 'disponible' || a.id === formData.appartement_id)
    );
    if (appartTypeFilter !== 'Tous') {
      apparts = apparts.filter(a => a.type_appart === appartTypeFilter);
    }
    return apparts.sort((a, b) => parseInt(a.numero_lot || 0) - parseInt(b.numero_lot || 0));
  }, [appartements, formData.appartement_id, appartTypeFilter]);

  const appartTypes = useMemo(() => {
    const types = [...new Set(appartements.filter(a => a.destination === 'Logement').map(a => a.type_appart))];
    return types.sort();
  }, [appartements]);

  const getAppartInfo = (id) => id ? appartements.find(a => a.id === id) : null;

  const openDialog = (client = null) => {
    if (client) {
      setEditingClient(client);
      setFormData({
        nom: client.nom || '', telephone: client.telephone || '',
        telephone2: client.telephone2 || '', email: client.email || '',
        salaire: client.salaire?.toString() || '',
        budget_min: client.budget_min?.toString() || '',
        budget_max: client.budget_max?.toString() || '',
        objectif: client.objectif || '', mode_paiement: client.mode_paiement || '',
        etage_souhaite: client.etage_souhaite || '',
        situation_familiale: client.situation_familiale || '',
        notes: client.notes || '', statut: client.statut || 'nouveau',
        appartement_id: client.appartement_id || '',
      });
    } else {
      setEditingClient(null);
      setFormData(emptyForm);
    }
    setAppartTypeFilter('Tous');
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = {
      ...formData,
      salaire: formData.salaire ? parseFloat(formData.salaire) : null,
      budget_min: formData.budget_min ? parseFloat(formData.budget_min) : null,
      budget_max: formData.budget_max ? parseFloat(formData.budget_max) : null,
      appartement_id: formData.appartement_id && formData.appartement_id !== 'none' ? formData.appartement_id : null,
      situation_familiale: formData.situation_familiale && formData.situation_familiale !== 'none' ? formData.situation_familiale : null,
      objectif: formData.objectif && formData.objectif !== 'none' ? formData.objectif : null,
      mode_paiement: formData.mode_paiement && formData.mode_paiement !== 'none' ? formData.mode_paiement : null,
      etage_souhaite: formData.etage_souhaite && formData.etage_souhaite !== 'none' ? formData.etage_souhaite : null,
      telephone2: formData.telephone2 || null,
    };
    try {
      if (editingClient) {
        await axios.put(`${API}/clients/${editingClient.id}`, payload);
      } else {
        await axios.post(`${API}/clients`, payload);
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
      await axios.delete(`${API}/clients/${id}`);
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(t('error'));
    }
  };

  const filteredClients = clients.filter((c) => {
    const matchSearch = c.nom?.toLowerCase().includes(search.toLowerCase()) ||
      c.telephone?.includes(search) || c.telephone2?.includes(search) || c.email?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || c.statut === statusFilter;
    return matchSearch && matchStatus;
  });

  const getStatusBadge = (s) => {
    const st = CLIENT_STATUSES.find(x => x.value === s);
    return st ? <Badge className={`${st.color} border text-xs`}>{st.label}</Badge> : <Badge className="text-xs">{s}</Badge>;
  };

  const formatDA = (v) => v ? new Intl.NumberFormat('fr-FR').format(v) + ' DA' : '';

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-5 fade-in" data-testid="clients-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            EDIMCO - {t('clients')}
          </h1>
          <p className="text-slate-500 mt-1">{clients.length} {t('clients').toLowerCase()}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => window.open(`${API}/export/clients/excel`, '_blank')} data-testid="export-excel">
            <FileSpreadsheet className="h-4 w-4 me-1" /> Excel
          </Button>
          <Button variant="outline" size="sm" onClick={() => window.open(`${API}/export/clients/pdf`, '_blank')} data-testid="export-pdf">
            <FileText className="h-4 w-4 me-1" /> PDF
          </Button>
          <Button size="sm" onClick={() => openDialog()} className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" data-testid="add-client-btn">
            <Plus className="h-4 w-4 me-1" /> {t('addClient')}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder={t('search')} value={search} onChange={e => setSearch(e.target.value)} className="ps-10" data-testid="search-clients" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40" data-testid="filter-status"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allStatuses')}</SelectItem>
            {CLIENT_STATUSES.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="bg-white rounded border border-slate-200 overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#1E3A5F]">
              <TableHead className="text-white text-xs font-medium">{t('name')}</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('phone')}</TableHead>
              <TableHead className="text-white text-xs font-medium">Objectif</TableHead>
              <TableHead className="text-white text-xs font-medium">Paiement</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('status')}</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('apartment')}</TableHead>
              <TableHead className="text-white text-xs font-medium w-[70px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredClients.length > 0 ? filteredClients.map(client => {
              const appart = getAppartInfo(client.appartement_id);
              return (
                <TableRow key={client.id} className="hover:bg-slate-50" data-testid={`client-row-${client.id}`}>
                  <TableCell>
                    <div>
                      <span className="font-medium text-sm">{client.nom}</span>
                      {client.objectif && (
                        <span className="text-xs text-slate-400 ms-1.5">({client.objectif})</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{client.telephone}</div>
                    {client.telephone2 && <div className="text-xs text-slate-400">{client.telephone2}</div>}
                  </TableCell>
                  <TableCell>
                    {client.objectif ? (
                      <Badge className={`text-xs border ${client.objectif === 'Investissement' ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-blue-50 text-blue-700 border-blue-200'}`}>
                        {client.objectif === 'Investissement' ? 'Invest.' : 'Achat'}
                      </Badge>
                    ) : <span className="text-slate-300 text-xs">-</span>}
                  </TableCell>
                  <TableCell>
                    {client.mode_paiement ? (
                      <span className="text-xs text-slate-600">{client.mode_paiement === 'Crédit bancaire' ? 'Crédit' : 'Auto.'}</span>
                    ) : <span className="text-slate-300 text-xs">-</span>}
                  </TableCell>
                  <TableCell>{getStatusBadge(client.statut)}</TableCell>
                  <TableCell>
                    {appart ? (
                      <div className="flex items-center gap-1">
                        <Home className="h-3 w-3 text-[#1E3A5F]" />
                        <span className="text-xs font-medium text-[#1E3A5F]">
                          Lot {appart.numero_lot} - {appart.bloc} - {appart.type_appart}
                        </span>
                      </div>
                    ) : <span className="text-slate-300 text-xs">-</span>}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-0.5">
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => openDialog(client)} data-testid={`edit-client-${client.id}`}>
                        <Pencil className="h-3 w-3 text-slate-500" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => handleDelete(client.id)} data-testid={`delete-client-${client.id}`}>
                        <Trash2 className="h-3 w-3 text-red-400" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            }) : (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-10 text-slate-400">{t('noClients')}</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F]">
              {editingClient ? t('editClient') : t('addClient')}
            </DialogTitle>
            <DialogDescription>{editingClient ? t('edit') : t('create')}</DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Nom */}
            <div className="space-y-1">
              <Label className="text-xs">{t('name')} *</Label>
              <Input value={formData.nom} onChange={e => setFormData({...formData, nom: e.target.value})} required className="h-9" data-testid="client-nom" />
            </div>

            {/* Telephones */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('phone')} 1 *</Label>
                <Input value={formData.telephone} onChange={e => setFormData({...formData, telephone: e.target.value})} required className="h-9" data-testid="client-telephone" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t('phone')} 2</Label>
                <Input value={formData.telephone2} onChange={e => setFormData({...formData, telephone2: e.target.value})} className="h-9" placeholder="Optionnel" data-testid="client-telephone2" />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <Label className="text-xs">{t('email')}</Label>
              <Input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="h-9" data-testid="client-email" />
            </div>

            {/* Statut + Situation */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('status')}</Label>
                <Select value={formData.statut} onValueChange={v => setFormData({...formData, statut: v})}>
                  <SelectTrigger className="h-9" data-testid="client-statut"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CLIENT_STATUSES.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t('situation')}</Label>
                <Select value={formData.situation_familiale || 'none'} onValueChange={v => setFormData({...formData, situation_familiale: v === 'none' ? '' : v})}>
                  <SelectTrigger className="h-9" data-testid="client-situation"><SelectValue placeholder="-" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-</SelectItem>
                    {SITUATIONS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Objectif */}
            <div className="space-y-1">
              <Label className="text-xs">Objectif</Label>
              <Select value={formData.objectif || 'none'} onValueChange={v => setFormData({...formData, objectif: v === 'none' ? '' : v})}>
                <SelectTrigger className="h-9" data-testid="client-objectif"><SelectValue placeholder="-" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">-</SelectItem>
                  {OBJECTIFS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {/* Salaire + Mode paiement */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('salary')} (DA)</Label>
                <Input type="number" value={formData.salaire} onChange={e => setFormData({...formData, salaire: e.target.value})} className="h-9" data-testid="client-salaire" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Mode de paiement</Label>
                <Select value={formData.mode_paiement || 'none'} onValueChange={v => setFormData({...formData, mode_paiement: v === 'none' ? '' : v})}>
                  <SelectTrigger className="h-9" data-testid="client-paiement"><SelectValue placeholder="-" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-</SelectItem>
                    {MODES_PAIEMENT.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Budget min/max */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Budget min (DA)</Label>
                <Input type="number" step="100000" min="0" value={formData.budget_min} onChange={e => setFormData({...formData, budget_min: e.target.value})} placeholder="ex: 2800000" className="h-9" data-testid="client-budget-min" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Budget max (DA)</Label>
                <Input type="number" step="100000" min="0" value={formData.budget_max} onChange={e => setFormData({...formData, budget_max: e.target.value})} placeholder="ex: 10000000" className="h-9" data-testid="client-budget-max" />
              </div>
            </div>

            {/* Etage souhaité */}
            <div className="space-y-1">
              <Label className="text-xs">Etage souhaité</Label>
              <Select value={formData.etage_souhaite || 'none'} onValueChange={v => setFormData({...formData, etage_souhaite: v === 'none' ? '' : v})}>
                <SelectTrigger className="h-9" data-testid="client-etage"><SelectValue placeholder="-" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">-</SelectItem>
                  {ETAGES.map(e => <SelectItem key={e} value={e}>{e}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {/* Appartement EDIMCO */}
            <div className="space-y-2 p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <Home className="h-4 w-4 text-[#1E3A5F]" />
                <Label className="text-xs font-semibold text-[#1E3A5F]">Appartement EDIMCO</Label>
              </div>
              
              <div className="flex gap-1 mb-2 flex-wrap">
                {['Tous', ...appartTypes].map(tp => (
                  <button type="button" key={tp} onClick={() => setAppartTypeFilter(tp)}
                    className={`px-2 py-0.5 text-xs rounded transition-colors ${
                      appartTypeFilter === tp ? 'bg-[#1E3A5F] text-white' : 'bg-white text-slate-500 border border-slate-200'
                    }`}>{tp}</button>
                ))}
              </div>

              <Select value={formData.appartement_id || 'none'} onValueChange={v => setFormData({...formData, appartement_id: v === 'none' ? '' : v})}>
                <SelectTrigger className="h-9 bg-white" data-testid="client-appartement"><SelectValue placeholder="Aucun" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Aucun appartement</SelectItem>
                  {availableApparts.map(a => (
                    <SelectItem key={a.id} value={a.id}>
                      Lot {a.numero_lot} | Bloc {a.bloc} | {a.type_appart} | {a.etage} | {a.surface_habitable?.toFixed(0)}m2
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {formData.appartement_id && formData.appartement_id !== 'none' && (() => {
                const sel = appartements.find(a => a.id === formData.appartement_id);
                if (!sel) return null;
                return (
                  <div className="mt-2 p-2 rounded bg-[#1E3A5F]/5 border border-[#1E3A5F]/20 text-xs">
                    <span className="font-bold text-[#1E3A5F]">Lot {sel.numero_lot}</span> - Bloc {sel.bloc} - {sel.type_appart} - {sel.etage}
                    <br />
                    <span className="text-slate-500">{sel.surface_habitable?.toFixed(2)}m2 hab.</span>
                  </div>
                );
              })()}
            </div>

            {/* Notes */}
            <div className="space-y-1">
              <Label className="text-xs">{t('notes')}</Label>
              <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} rows={2} className="text-sm" data-testid="client-notes" />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>{t('cancel')}</Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-client-btn">
                {saving && <Loader2 className="h-4 w-4 animate-spin me-2" />}{t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
