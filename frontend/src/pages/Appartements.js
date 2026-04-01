import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Plus, Pencil, Trash2, Building2, Loader2, Home, FileSpreadsheet } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const APPART_TYPES = ['F1', 'F2', 'F3', 'F4', 'F5', 'Studio', 'Duplex'];

export function Appartements() {
  const [appartements, setAppartements] = useState([]);
  const [residences, setResidences] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedResidence, setSelectedResidence] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingAppart, setEditingAppart] = useState(null);
  const [saving, setSaving] = useState(false);
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();

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
    surface: '',
    description: '',
    statut: 'disponible',
    client_id: '',
  });

  const fetchData = async () => {
    try {
      const [appartsRes, residencesRes, clientsRes] = await Promise.all([
        axios.get(`${API}/appartements`, { withCredentials: true }),
        axios.get(`${API}/residences`, { withCredentials: true }),
        axios.get(`${API}/clients`, { withCredentials: true }),
      ]);
      setAppartements(appartsRes.data);
      setResidences(residencesRes.data);
      setClients(clientsRes.data);
      
      if (!selectedResidence && residencesRes.data.length > 0) {
        setSelectedResidence(residencesRes.data[0].id);
      }
    } catch (e) {
      toast.error(t('error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (lastMessage?.type?.includes('appartement') || lastMessage?.type?.includes('residence')) {
      fetchData();
    }
  }, [lastMessage]);

  const resetForm = () => {
    setFormData({
      residence_id: selectedResidence || '',
      type_appart: 'F2',
      prix: '',
      etage: '',
      surface: '',
      description: '',
      statut: 'disponible',
      client_id: '',
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
        surface: appart.surface?.toString() || '',
        description: appart.description || '',
        statut: appart.statut || 'disponible',
        client_id: appart.client_id || '',
      });
    } else {
      resetForm();
      setFormData(f => ({ ...f, residence_id: selectedResidence || '' }));
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      ...formData,
      prix: parseFloat(formData.prix),
      etage: parseInt(formData.etage),
      surface: formData.surface ? parseFloat(formData.surface) : null,
      client_id: formData.client_id && formData.client_id !== 'none' ? formData.client_id : null,
    };

    try {
      if (editingAppart) {
        await axios.put(`${API}/appartements/${editingAppart.id}`, payload, { withCredentials: true });
        toast.success(t('success'));
      } else {
        await axios.post(`${API}/appartements`, payload, { withCredentials: true });
        toast.success(t('success'));
      }
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
    const status = APPART_STATUSES.find((s) => s.value === statut);
    return status ? (
      <Badge className={`${status.color} border`}>{status.label}</Badge>
    ) : (
      <Badge>{statut}</Badge>
    );
  };

  const getClientName = (clientId) => {
    if (!clientId) return null;
    const client = clients.find((c) => c.id === clientId);
    return client?.nom || null;
  };

  const filteredAppartements = appartements.filter(
    (a) => a.residence_id === selectedResidence
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" />
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in" data-testid="appartements-page">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            {t('apartments')}
          </h1>
          <p className="text-slate-500 mt-1">{appartements.length} {t('apartments').toLowerCase()}</p>
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

      {/* Residence Tabs */}
      {residences.length > 0 ? (
        <Tabs value={selectedResidence} onValueChange={setSelectedResidence}>
          <TabsList className="bg-white border border-slate-200">
            {residences.map((residence) => (
              <TabsTrigger
                key={residence.id}
                value={residence.id}
                className="data-[state=active]:bg-[#1E3A5F] data-[state=active]:text-white"
                data-testid={`tab-${residence.nom.toLowerCase().replace(/\s/g, '-')}`}
              >
                <Building2 className="h-4 w-4 me-2" />
                {residence.nom}
              </TabsTrigger>
            ))}
          </TabsList>

          {residences.map((residence) => (
            <TabsContent key={residence.id} value={residence.id} className="mt-6">
              {/* Stats for this residence */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <Card className="bg-emerald-50 border-emerald-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-emerald-600">{t('available')}</p>
                        <p className="text-2xl font-light text-emerald-700">
                          {filteredAppartements.filter(a => a.statut === 'disponible').length}
                        </p>
                      </div>
                      <Home className="h-8 w-8 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-amber-50 border-amber-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-amber-600">{t('reserved')}</p>
                        <p className="text-2xl font-light text-amber-700">
                          {filteredAppartements.filter(a => a.statut === 'réservé').length}
                        </p>
                      </div>
                      <Home className="h-8 w-8 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-100 border-slate-200">
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-600">{t('sold')}</p>
                        <p className="text-2xl font-light text-slate-700">
                          {filteredAppartements.filter(a => a.statut === 'vendu').length}
                        </p>
                      </div>
                      <Home className="h-8 w-8 text-slate-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Apartments Grid */}
              {filteredAppartements.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredAppartements.map((appart) => (
                    <Card key={appart.id} className="card-luxury" data-testid={`appart-card-${appart.id}`}>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit']">
                            {appart.type_appart}
                          </CardTitle>
                          {getStatusBadge(appart.statut)}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-500">{t('price')}</span>
                            <span className="font-medium text-[#1E3A5F]">{appart.prix?.toLocaleString('fr-FR')} DA</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">{t('floor')}</span>
                            <span className="font-medium">{appart.etage}</span>
                          </div>
                          {appart.surface && (
                            <div className="flex justify-between">
                              <span className="text-slate-500">{t('surface')}</span>
                              <span className="font-medium">{appart.surface} m²</span>
                            </div>
                          )}
                          {appart.client_id && (
                            <div className="flex justify-between">
                              <span className="text-slate-500">Client</span>
                              <span className="font-medium text-[#C41E3A]">{getClientName(appart.client_id)}</span>
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2 mt-4 pt-4 border-t border-slate-100">
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1"
                            onClick={() => openDialog(appart)}
                            data-testid={`edit-appart-${appart.id}`}
                          >
                            <Pencil className="h-3 w-3 me-1" />
                            {t('edit')}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-red-500 hover:text-red-700"
                            onClick={() => handleDelete(appart.id)}
                            data-testid={`delete-appart-${appart.id}`}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="bg-slate-50">
                  <CardContent className="py-12 text-center text-slate-500">
                    <Building2 className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p>{t('noApartments')}</p>
                    <Button onClick={() => openDialog()} className="mt-4" variant="outline">
                      <Plus className="h-4 w-4 me-2" />
                      {t('addApartment')}
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <Card className="bg-slate-50">
          <CardContent className="py-12 text-center text-slate-500">
            <Building2 className="h-12 w-12 mx-auto mb-4 text-slate-300" />
            <p>{t('noApartments')}</p>
          </CardContent>
        </Card>
      )}

      {/* Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F]">
              {editingAppart ? t('editApartment') : t('addApartment')}
            </DialogTitle>
            <DialogDescription>
              {editingAppart ? t('edit') : t('create')}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="residence">{t('residence')} *</Label>
                <Select
                  value={formData.residence_id}
                  onValueChange={(v) => setFormData({ ...formData, residence_id: v })}
                >
                  <SelectTrigger data-testid="appart-residence">
                    <SelectValue placeholder={t('none')} />
                  </SelectTrigger>
                  <SelectContent>
                    {residences.map((r) => (
                      <SelectItem key={r.id} value={r.id}>{r.nom}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">{t('type')} *</Label>
                <Select
                  value={formData.type_appart}
                  onValueChange={(v) => setFormData({ ...formData, type_appart: v })}
                >
                  <SelectTrigger data-testid="appart-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {APPART_TYPES.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="prix">{t('price')} (DA) *</Label>
                <Input
                  id="prix"
                  type="number"
                  value={formData.prix}
                  onChange={(e) => setFormData({ ...formData, prix: e.target.value })}
                  required
                  data-testid="appart-prix"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="etage">{t('floor')} *</Label>
                <Input
                  id="etage"
                  type="number"
                  value={formData.etage}
                  onChange={(e) => setFormData({ ...formData, etage: e.target.value })}
                  required
                  data-testid="appart-etage"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="surface">{t('surface')} (m²)</Label>
                <Input
                  id="surface"
                  type="number"
                  value={formData.surface}
                  onChange={(e) => setFormData({ ...formData, surface: e.target.value })}
                  data-testid="appart-surface"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="statut">{t('status')} *</Label>
                <Select
                  value={formData.statut}
                  onValueChange={(v) => setFormData({ ...formData, statut: v })}
                >
                  <SelectTrigger data-testid="appart-statut">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {APPART_STATUSES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {(formData.statut === 'réservé' || formData.statut === 'vendu') && (
              <div className="space-y-2">
                <Label htmlFor="client">Client</Label>
                <Select
                  value={formData.client_id}
                  onValueChange={(v) => setFormData({ ...formData, client_id: v })}
                >
                  <SelectTrigger data-testid="appart-client">
                    <SelectValue placeholder={t('none')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">{t('none')}</SelectItem>
                    {clients.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.nom} - {c.telephone}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="description">{t('description')}</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                data-testid="appart-description"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                {t('cancel')}
              </Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-appart-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin me-2" /> : null}
                {t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
