import { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
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
import { Plus, Pencil, Trash2, Search, Loader2, FileSpreadsheet, FileText, Home, AlertTriangle, X } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

const OBJECTIFS = ['Achat personnel', 'Investissement'];
const MODES_PAIEMENT = ['Autofinancement', 'Crédit bancaire'];
const ETAGES = ['Etage 02', 'Etage 03', 'Etage 04', 'Etage 05', 'Etage 06', 'Etage 07', 'Etage 08', 'Etage 09', 'Etage 10', 'Etage 11', 'Duplex 10-11'];
const SITUATIONS = ['Célibataire', 'Marié(e)', 'Divorcé(e)', 'Veuf/Veuve', 'En couple'];

export function Clients() {
  const { user } = useAuth();
  const [clients, setClients] = useState([]);
  const [appartements, setAppartements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [saving, setSaving] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();

  // Read filter from URL params (from dashboard click)
  useEffect(() => {
    const statut = searchParams.get('statut');
    if (statut) setStatusFilter(statut);
  }, [searchParams]);

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
    appartement_ids: [],
  };

  const [formData, setFormData] = useState(emptyForm);
  const [appartTypeFilter, setAppartTypeFilter] = useState('Tous');

  const fetchData = async () => {
    try {
      const [c, a] = await Promise.all([
        axios.get(`${API}/clients`),
        axios.get(`${API}/appartements`),
      ]);
      setClients(c.data || []);
      setAppartements(a.data || []);
    } catch (e) {
      console.error('Fetch error:', e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => {
    if (lastMessage?.type?.includes('client') || lastMessage?.type?.includes('appartement') || lastMessage?.type === 'new_lead') fetchData();
  }, [lastMessage]);

  const availableApparts = useMemo(() => {
    const selectedIds = formData.appartement_ids || [];
    let apparts = appartements.filter(a =>
      a.destination === 'Logement' &&
      (a.statut === 'disponible' || selectedIds.includes(a.id))
    );
    if (appartTypeFilter !== 'Tous') {
      apparts = apparts.filter(a => a.type_appart === appartTypeFilter);
    }
    return apparts.sort((a, b) => parseInt(a.numero_lot || 0) - parseInt(b.numero_lot || 0));
  }, [appartements, formData.appartement_ids, appartTypeFilter]);

  const appartTypes = useMemo(() => {
    const types = [...new Set(appartements.filter(a => a.destination === 'Logement').map(a => a.type_appart))];
    return types.sort();
  }, [appartements]);

  const openDialog = (client = null) => {
    setDuplicateWarning(null);
    if (client) {
      setEditingClient(client);
      const ids = client.appartement_ids?.length > 0 ? client.appartement_ids : (client.appartement_id ? [client.appartement_id] : []);
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
        appartement_ids: ids,
      });
    } else {
      setEditingClient(null);
      setFormData(emptyForm);
    }
    setAppartTypeFilter('Tous');
    setIsDialogOpen(true);
  };

  const addAppartement = (apId) => {
    if (apId && apId !== 'none' && !formData.appartement_ids.includes(apId)) {
      setFormData({ ...formData, appartement_ids: [...formData.appartement_ids, apId] });
    }
  };

  const removeAppartement = (apId) => {
    setFormData({ ...formData, appartement_ids: formData.appartement_ids.filter(id => id !== apId) });
  };

  const handleSubmit = async (e, forceCreate = false) => {
    e?.preventDefault();
    setSaving(true);
    const payload = {
      ...formData,
      salaire: formData.salaire ? parseFloat(formData.salaire) : null,
      budget_min: formData.budget_min ? parseFloat(formData.budget_min) : null,
      budget_max: formData.budget_max ? parseFloat(formData.budget_max) : null,
      appartement_ids: formData.appartement_ids.filter(id => id && id !== 'none'),
      situation_familiale: formData.situation_familiale && formData.situation_familiale !== 'none' ? formData.situation_familiale : null,
      objectif: formData.objectif && formData.objectif !== 'none' ? formData.objectif : null,
      mode_paiement: formData.mode_paiement && formData.mode_paiement !== 'none' ? formData.mode_paiement : null,
      etage_souhaite: formData.etage_souhaite && formData.etage_souhaite !== 'none' ? formData.etage_souhaite : null,
      telephone2: formData.telephone2 || null,
      force_create: forceCreate,
    };
    try {
      let res;
      if (editingClient) {
        res = await axios.put(`${API}/clients/${editingClient.id}`, payload);
      } else {
        res = await axios.post(`${API}/clients`, payload);
      }
      // Check for duplicate warning
      if (res.data?.needs_confirmation) {
        setDuplicateWarning(res.data.duplicates);
        setSaving(false);
        return;
      }
      // Check for approval required
      if (res.data?.approval_required) {
        toast.info(t('approvalRequired'));
      } else {
        toast.success(t('success'));
      }
      setIsDialogOpen(false);
      setDuplicateWarning(null);
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
      const res = await axios.delete(`${API}/clients/${id}`);
      if (res.data?.approval_required) {
        toast.info(t('approvalRequired'));
      } else {
        toast.success(t('success'));
      }
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    }
  };

  const filteredClients = clients.filter((c) => {
    const matchSearch = c.nom?.toLowerCase().includes(search.toLowerCase()) ||
      c.telephone?.includes(search) || c.telephone2?.includes(search) ||
      c.email?.toLowerCase().includes(search.toLowerCase()) ||
      c.reference?.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || c.statut === statusFilter;
    return matchSearch && matchStatus;
  });

  const getStatusBadge = (s) => {
    const st = CLIENT_STATUSES.find(x => x.value === s);
    return st ? <Badge className={`${st.color} border text-xs`}>{st.label}</Badge> : <Badge className="text-xs">{s}</Badge>;
  };

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
              <TableHead className="text-white text-xs font-medium w-[60px]">{t('reference')}</TableHead>
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
              const apInfos = client.appartements_info || [];
              return (
                <TableRow key={client.id} className="hover:bg-slate-50" data-testid={`client-row-${client.id}`}>
                  <TableCell>
                    <span className="font-mono text-xs font-bold text-[#1E3A5F]">{client.reference || '-'}</span>
                  </TableCell>
                  <TableCell>
                    <span className="font-medium text-sm">{client.nom}</span>
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
                    {apInfos.length > 0 ? (
                      <div className="space-y-0.5">
                        {apInfos.map(ap => (
                          <div key={ap.id} className="flex items-center gap-1">
                            <Home className="h-3 w-3 text-[#1E3A5F]" />
                            <span className="text-xs font-medium text-[#1E3A5F]">
                              Lot {ap.numero_lot} - {ap.bloc}
                            </span>
                          </div>
                        ))}
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
                <TableCell colSpan={8} className="text-center py-10 text-slate-400">{t('noClients')}</TableCell>
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

          {/* Duplicate Warning */}
          {duplicateWarning && (
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3" data-testid="duplicate-warning">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <span className="font-medium text-sm text-amber-800">Doublons potentiels détectés !</span>
              </div>
              <div className="space-y-1 mb-3">
                {duplicateWarning.map(d => (
                  <div key={d.id} className="text-xs text-amber-700 bg-white p-2 rounded border border-amber-200">
                    <span className="font-medium">{d.nom}</span> - {d.telephone} 
                    <span className="text-amber-500 ms-1">(Similitude: {d.reasons.join(', ')})</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="text-xs" onClick={() => { setDuplicateWarning(null); setIsDialogOpen(false); }}>Annuler</Button>
                <Button size="sm" className="bg-amber-600 hover:bg-amber-700 text-xs" onClick={(e) => handleSubmit(e, true)} data-testid="force-create-btn">
                  Créer quand même
                </Button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1">
              <Label className="text-xs">{t('name')} *</Label>
              <Input value={formData.nom} onChange={e => setFormData({...formData, nom: e.target.value})} required className="h-9" data-testid="client-nom" />
            </div>

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

            <div className="space-y-1">
              <Label className="text-xs">{t('email')}</Label>
              <Input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="h-9" data-testid="client-email" />
            </div>

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

            {/* Multi-Apartment Selection */}
            <div className="space-y-2 p-3 rounded-lg bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <Home className="h-4 w-4 text-[#1E3A5F]" />
                <Label className="text-xs font-semibold text-[#1E3A5F]">Appartements EDIMCO</Label>
                {formData.appartement_ids.length > 0 && (
                  <Badge className="bg-[#1E3A5F] text-white text-xs">{formData.appartement_ids.length}</Badge>
                )}
              </div>
              
              <div className="flex gap-1 mb-2 flex-wrap">
                {['Tous', ...appartTypes].map(tp => (
                  <button type="button" key={tp} onClick={() => setAppartTypeFilter(tp)}
                    className={`px-2 py-0.5 text-xs rounded transition-colors ${
                      appartTypeFilter === tp ? 'bg-[#1E3A5F] text-white' : 'bg-white text-slate-500 border border-slate-200'
                    }`}>{tp}</button>
                ))}
              </div>

              {/* Add apartment selector */}
              <Select value="" onValueChange={addAppartement}>
                <SelectTrigger className="h-9 bg-white" data-testid="client-add-appartement"><SelectValue placeholder="Ajouter un appartement..." /></SelectTrigger>
                <SelectContent>
                  {availableApparts.filter(a => !formData.appartement_ids.includes(a.id)).map(a => (
                    <SelectItem key={a.id} value={a.id}>
                      Lot {a.numero_lot} | Bloc {a.bloc} | {a.type_appart} | {a.etage} | {a.surface_habitable?.toFixed(0)}m2
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Selected apartments list */}
              {formData.appartement_ids.length > 0 && (
                <div className="space-y-1 mt-2">
                  {formData.appartement_ids.map(apId => {
                    const sel = appartements.find(a => a.id === apId);
                    if (!sel) return null;
                    return (
                      <div key={apId} className="flex items-center justify-between p-2 rounded bg-[#1E3A5F]/5 border border-[#1E3A5F]/20">
                        <span className="text-xs">
                          <span className="font-bold text-[#1E3A5F]">Lot {sel.numero_lot}</span> - Bloc {sel.bloc} - {sel.type_appart} - {sel.etage}
                          <span className="text-slate-500 ms-1">({sel.surface_habitable?.toFixed(0)}m2)</span>
                        </span>
                        <button type="button" onClick={() => removeAppartement(apId)} className="text-red-400 hover:text-red-600">
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

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
