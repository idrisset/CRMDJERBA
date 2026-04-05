import { useState, useEffect } from 'react';
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
import {
  Plus, Pencil, Trash2, Search, Loader2, FileSpreadsheet, FileText,
  MapPin, Home, TrendingUp, BarChart3, Users, DollarSign
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPES_LOGEMENT = ['F2', 'F3', 'F4', 'F5', 'Duplex', 'Studio', 'Villa', 'Local commercial', 'Autre'];
const SOURCES = ['Foire', 'Réseaux sociaux', 'Recommandation', 'Visite directe', 'Appel téléphonique', 'Site web', 'Autre'];
const OBJECTIFS = ['Achat personnel', 'Investissement'];
const MODES_PAIEMENT = ['Autofinancement', 'Crédit bancaire'];
const SITUATIONS = ['Célibataire', 'Marié(e)', 'Divorcé(e)', 'Veuf/Veuve', 'En couple'];

export function Prospects() {
  const [prospects, setProspects] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [villeFilter, setVilleFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProspect, setEditingProspect] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

  const emptyForm = {
    nom: '', telephone: '', telephone2: '', email: '',
    ville: '', quartier: '', type_logement: '',
    etage_souhaite: '', nombre_pieces: '',
    budget_min: '', budget_max: '',
    mode_paiement: '', objectif: '',
    situation_familiale: '', notes: '', source: 'Foire',
  };

  const [formData, setFormData] = useState(emptyForm);

  const fetchData = async () => {
    try {
      const [pRes, aRes] = await Promise.all([
        axios.get(`${API}/prospects`),
        axios.get(`${API}/prospects/analytics`),
      ]);
      setProspects(pRes.data || []);
      setAnalytics(aRes.data || null);
    } catch (e) {
      if (e.response?.status !== 401) console.error('Fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => {
    if (lastMessage?.type?.includes('prospect')) fetchData();
  }, [lastMessage]);

  const uniqueVilles = [...new Set(prospects.map(p => p.ville).filter(Boolean))].sort();
  const uniqueTypes = [...new Set(prospects.map(p => p.type_logement).filter(Boolean))].sort();

  const openDialog = (prospect = null) => {
    if (prospect) {
      setEditingProspect(prospect);
      setFormData({
        nom: prospect.nom || '', telephone: prospect.telephone || '',
        telephone2: prospect.telephone2 || '', email: prospect.email || '',
        ville: prospect.ville || '', quartier: prospect.quartier || '',
        type_logement: prospect.type_logement || '',
        etage_souhaite: prospect.etage_souhaite || '',
        nombre_pieces: prospect.nombre_pieces?.toString() || '',
        budget_min: prospect.budget_min?.toString() || '',
        budget_max: prospect.budget_max?.toString() || '',
        mode_paiement: prospect.mode_paiement || '',
        objectif: prospect.objectif || '',
        situation_familiale: prospect.situation_familiale || '',
        notes: prospect.notes || '', source: prospect.source || 'Foire',
      });
    } else {
      setEditingProspect(null);
      setFormData(emptyForm);
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = {
      ...formData,
      nombre_pieces: formData.nombre_pieces ? parseInt(formData.nombre_pieces) : null,
      budget_min: formData.budget_min ? parseFloat(formData.budget_min) : null,
      budget_max: formData.budget_max ? parseFloat(formData.budget_max) : null,
      telephone2: formData.telephone2 || null,
      email: formData.email || null,
      ville: formData.ville || null,
      quartier: formData.quartier || null,
      type_logement: formData.type_logement && formData.type_logement !== 'none' ? formData.type_logement : null,
      etage_souhaite: formData.etage_souhaite || null,
      mode_paiement: formData.mode_paiement && formData.mode_paiement !== 'none' ? formData.mode_paiement : null,
      objectif: formData.objectif && formData.objectif !== 'none' ? formData.objectif : null,
      situation_familiale: formData.situation_familiale && formData.situation_familiale !== 'none' ? formData.situation_familiale : null,
      source: formData.source && formData.source !== 'none' ? formData.source : null,
    };
    try {
      if (editingProspect) {
        await axios.put(`${API}/prospects/${editingProspect.id}`, payload);
      } else {
        await axios.post(`${API}/prospects`, payload);
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
      await axios.delete(`${API}/prospects/${id}`);
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(t('error'));
    }
  };

  const filteredProspects = prospects.filter((p) => {
    const matchSearch = p.nom?.toLowerCase().includes(search.toLowerCase()) ||
      p.telephone?.includes(search) || p.ville?.toLowerCase().includes(search.toLowerCase()) ||
      p.quartier?.toLowerCase().includes(search.toLowerCase());
    const matchVille = villeFilter === 'all' || p.ville === villeFilter;
    const matchType = typeFilter === 'all' || p.type_logement === typeFilter;
    return matchSearch && matchVille && matchType;
  });

  const formatDA = (v) => v ? new Intl.NumberFormat('fr-FR').format(v) + ' DA' : '';

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-5 fade-in" data-testid="prospects-page">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            {t('bigData')} - {t('prospects')}
          </h1>
          <p className="text-slate-500 mt-1">{prospects.length} {t('prospects').toLowerCase()}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => setShowAnalytics(!showAnalytics)} data-testid="toggle-analytics">
            <BarChart3 className="h-4 w-4 me-1" /> {t('analytics')}
          </Button>
          <Button variant="outline" size="sm" onClick={() => window.open(`${API}/export/prospects/excel`, '_blank')} data-testid="export-prospects-excel">
            <FileSpreadsheet className="h-4 w-4 me-1" /> Excel
          </Button>
          <Button variant="outline" size="sm" onClick={() => window.open(`${API}/export/prospects/pdf`, '_blank')} data-testid="export-prospects-pdf">
            <FileText className="h-4 w-4 me-1" /> PDF
          </Button>
          <Button size="sm" onClick={() => openDialog()} className="bg-[#C41E3A] hover:bg-[#9A152C]" data-testid="add-prospect-btn">
            <Plus className="h-4 w-4 me-1" /> {t('addProspect')}
          </Button>
        </div>
      </div>

      {/* Analytics Section */}
      {showAnalytics && analytics && (
        <div className="space-y-4" data-testid="analytics-section">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center">
                    <Users className="h-5 w-5 text-[#1E3A5F]" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">{t('totalProspects')}</p>
                    <p className="text-xl font-semibold text-[#1E3A5F]">{analytics.total}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                    <MapPin className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">{t('citiesCovered')}</p>
                    <p className="text-xl font-semibold text-emerald-600">{analytics.top_villes?.length || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-amber-50 flex items-center justify-center">
                    <Home className="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">{t('topType')}</p>
                    <p className="text-lg font-semibold text-amber-600">{analytics.top_types?.[0]?.name || '-'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-red-50 flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-[#C41E3A]" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500">{t('avgBudget')}</p>
                    <p className="text-sm font-semibold text-[#C41E3A]">{formatDA(Math.round(analytics.budget_avg?.avg_max || 0))}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Analytics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Top Villes */}
            {analytics.top_villes?.length > 0 && (
              <Card className="border-slate-200">
                <CardContent className="p-4">
                  <h3 className="text-sm font-semibold text-[#1E3A5F] mb-3 flex items-center gap-2">
                    <MapPin className="h-4 w-4" /> {t('topCities')}
                  </h3>
                  <div className="space-y-2">
                    {analytics.top_villes.slice(0, 5).map((v, i) => (
                      <div key={i} className="flex justify-between items-center">
                        <span className="text-sm text-slate-700">{v.name}</span>
                        <Badge className="bg-[#1E3A5F]/10 text-[#1E3A5F] border-0 text-xs">{v.count}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Types */}
            {analytics.top_types?.length > 0 && (
              <Card className="border-slate-200">
                <CardContent className="p-4">
                  <h3 className="text-sm font-semibold text-[#1E3A5F] mb-3 flex items-center gap-2">
                    <Home className="h-4 w-4" /> {t('demandByType')}
                  </h3>
                  <div className="space-y-2">
                    {analytics.top_types.map((tp, i) => {
                      const maxCount = analytics.top_types[0]?.count || 1;
                      const pct = Math.round((tp.count / maxCount) * 100);
                      return (
                        <div key={i}>
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm text-slate-700">{tp.name}</span>
                            <span className="text-xs text-slate-500">{tp.count}</span>
                          </div>
                          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-[#C41E3A] rounded-full transition-all" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Zones */}
            {analytics.top_zones?.length > 0 && (
              <Card className="border-slate-200">
                <CardContent className="p-4">
                  <h3 className="text-sm font-semibold text-[#1E3A5F] mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" /> {t('hotZones')}
                  </h3>
                  <div className="space-y-2">
                    {analytics.top_zones.slice(0, 5).map((z, i) => (
                      <div key={i} className="flex justify-between items-center">
                        <span className="text-sm text-slate-700">{z.ville}, {z.quartier}</span>
                        <Badge className="bg-[#C41E3A]/10 text-[#C41E3A] border-0 text-xs">{z.count}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder={t('searchProspect')} value={search} onChange={e => setSearch(e.target.value)} className="ps-10" data-testid="search-prospects" />
        </div>
        <Select value={villeFilter} onValueChange={setVilleFilter}>
          <SelectTrigger className="w-40" data-testid="filter-ville"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allCities')}</SelectItem>
            {uniqueVilles.map(v => <SelectItem key={v} value={v}>{v}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-40" data-testid="filter-type"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allTypes')}</SelectItem>
            {uniqueTypes.map(tp => <SelectItem key={tp} value={tp}>{tp}</SelectItem>)}
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
              <TableHead className="text-white text-xs font-medium">{t('city')}</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('neighborhood')}</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('housingType')}</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('rooms')}</TableHead>
              <TableHead className="text-white text-xs font-medium">{t('source')}</TableHead>
              <TableHead className="text-white text-xs font-medium w-[70px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredProspects.length > 0 ? filteredProspects.map(prospect => (
              <TableRow key={prospect.id} className="hover:bg-slate-50" data-testid={`prospect-row-${prospect.id}`}>
                <TableCell>
                  <div>
                    <span className="font-medium text-sm">{prospect.nom}</span>
                    {prospect.objectif && (
                      <span className="text-xs text-slate-400 ms-1.5">({prospect.objectif === 'Investissement' ? 'Invest.' : 'Achat'})</span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="text-sm">{prospect.telephone}</div>
                  {prospect.telephone2 && <div className="text-xs text-slate-400">{prospect.telephone2}</div>}
                </TableCell>
                <TableCell>
                  {prospect.ville ? (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3 text-emerald-500" />
                      <span className="text-sm">{prospect.ville}</span>
                    </div>
                  ) : <span className="text-slate-300 text-xs">-</span>}
                </TableCell>
                <TableCell>
                  <span className="text-sm">{prospect.quartier || <span className="text-slate-300">-</span>}</span>
                </TableCell>
                <TableCell>
                  {prospect.type_logement ? (
                    <Badge className="bg-amber-50 text-amber-700 border border-amber-200 text-xs">{prospect.type_logement}</Badge>
                  ) : <span className="text-slate-300 text-xs">-</span>}
                </TableCell>
                <TableCell>
                  <span className="text-sm">{prospect.nombre_pieces || <span className="text-slate-300">-</span>}</span>
                </TableCell>
                <TableCell>
                  {prospect.source ? (
                    <Badge className="bg-slate-100 text-slate-600 border border-slate-200 text-xs">{prospect.source}</Badge>
                  ) : <span className="text-slate-300 text-xs">-</span>}
                </TableCell>
                <TableCell>
                  <div className="flex gap-0.5">
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => openDialog(prospect)} data-testid={`edit-prospect-${prospect.id}`}>
                      <Pencil className="h-3 w-3 text-slate-500" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => handleDelete(prospect.id)} data-testid={`delete-prospect-${prospect.id}`}>
                      <Trash2 className="h-3 w-3 text-red-400" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-10 text-slate-400">{t('noProspects')}</TableCell>
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
              {editingProspect ? t('editProspect') : t('addProspect')}
            </DialogTitle>
            <DialogDescription>{editingProspect ? t('edit') : t('create')}</DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Nom */}
            <div className="space-y-1">
              <Label className="text-xs">{t('name')} *</Label>
              <Input value={formData.nom} onChange={e => setFormData({...formData, nom: e.target.value})} required className="h-9" data-testid="prospect-nom" />
            </div>

            {/* Telephones */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('phone')} 1 *</Label>
                <Input value={formData.telephone} onChange={e => setFormData({...formData, telephone: e.target.value})} required className="h-9" data-testid="prospect-telephone" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t('phone')} 2</Label>
                <Input value={formData.telephone2} onChange={e => setFormData({...formData, telephone2: e.target.value})} className="h-9" placeholder="Optionnel" data-testid="prospect-telephone2" />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <Label className="text-xs">{t('email')}</Label>
              <Input type="email" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} className="h-9" data-testid="prospect-email" />
            </div>

            {/* Ville + Quartier */}
            <div className="space-y-2 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200/50">
              <div className="flex items-center gap-2 mb-1">
                <MapPin className="h-4 w-4 text-emerald-600" />
                <Label className="text-xs font-semibold text-emerald-700">{t('desiredLocation')}</Label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">{t('city')} *</Label>
                  <Input value={formData.ville} onChange={e => setFormData({...formData, ville: e.target.value})} className="h-9 bg-white" placeholder="ex: Bejaia" data-testid="prospect-ville" />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">{t('neighborhood')}</Label>
                  <Input value={formData.quartier} onChange={e => setFormData({...formData, quartier: e.target.value})} className="h-9 bg-white" placeholder="ex: Ihaddaden" data-testid="prospect-quartier" />
                </div>
              </div>
            </div>

            {/* Type logement + Nombre pieces */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t('housingType')}</Label>
                <Select value={formData.type_logement || 'none'} onValueChange={v => setFormData({...formData, type_logement: v === 'none' ? '' : v})}>
                  <SelectTrigger className="h-9" data-testid="prospect-type"><SelectValue placeholder="-" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-</SelectItem>
                    {TYPES_LOGEMENT.map(tp => <SelectItem key={tp} value={tp}>{tp}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t('rooms')}</Label>
                <Input type="number" min="1" max="10" value={formData.nombre_pieces} onChange={e => setFormData({...formData, nombre_pieces: e.target.value})} className="h-9" data-testid="prospect-pieces" />
              </div>
            </div>

            {/* Etage */}
            <div className="space-y-1">
              <Label className="text-xs">{t('desiredFloor')}</Label>
              <Input value={formData.etage_souhaite} onChange={e => setFormData({...formData, etage_souhaite: e.target.value})} className="h-9" placeholder="ex: 3, RDC, Haut" data-testid="prospect-etage" />
            </div>

            {/* Objectif + Situation */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Objectif</Label>
                <Select value={formData.objectif || 'none'} onValueChange={v => setFormData({...formData, objectif: v === 'none' ? '' : v})}>
                  <SelectTrigger className="h-9" data-testid="prospect-objectif"><SelectValue placeholder="-" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-</SelectItem>
                    {OBJECTIFS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t('situation')}</Label>
                <Select value={formData.situation_familiale || 'none'} onValueChange={v => setFormData({...formData, situation_familiale: v === 'none' ? '' : v})}>
                  <SelectTrigger className="h-9" data-testid="prospect-situation"><SelectValue placeholder="-" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-</SelectItem>
                    {SITUATIONS.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Budget min/max */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Budget min (DA)</Label>
                <Input type="number" step="100000" min="0" value={formData.budget_min} onChange={e => setFormData({...formData, budget_min: e.target.value})} placeholder="ex: 2800000" className="h-9" data-testid="prospect-budget-min" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Budget max (DA)</Label>
                <Input type="number" step="100000" min="0" value={formData.budget_max} onChange={e => setFormData({...formData, budget_max: e.target.value})} placeholder="ex: 10000000" className="h-9" data-testid="prospect-budget-max" />
              </div>
            </div>

            {/* Mode paiement */}
            <div className="space-y-1">
              <Label className="text-xs">{t('paymentMethod')}</Label>
              <Select value={formData.mode_paiement || 'none'} onValueChange={v => setFormData({...formData, mode_paiement: v === 'none' ? '' : v})}>
                <SelectTrigger className="h-9" data-testid="prospect-paiement"><SelectValue placeholder="-" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">-</SelectItem>
                  {MODES_PAIEMENT.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {/* Source */}
            <div className="space-y-1">
              <Label className="text-xs">{t('source')}</Label>
              <Select value={formData.source || 'none'} onValueChange={v => setFormData({...formData, source: v === 'none' ? '' : v})}>
                <SelectTrigger className="h-9" data-testid="prospect-source"><SelectValue placeholder="-" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">-</SelectItem>
                  {SOURCES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {/* Notes */}
            <div className="space-y-1">
              <Label className="text-xs">{t('notes')}</Label>
              <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} rows={2} className="text-sm" data-testid="prospect-notes" />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>{t('cancel')}</Button>
              <Button type="submit" className="bg-[#C41E3A] hover:bg-[#9A152C]" disabled={saving} data-testid="save-prospect-btn">
                {saving && <Loader2 className="h-4 w-4 animate-spin me-2" />}{t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
