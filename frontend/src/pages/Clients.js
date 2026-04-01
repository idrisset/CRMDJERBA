import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
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
import { Plus, Pencil, Trash2, Search, Loader2, Download, FileSpreadsheet, FileText, MessageSquare, Flame, Thermometer } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function Clients() {
  const [clients, setClients] = useState([]);
  const [appartements, setAppartements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tempFilter, setTempFilter] = useState('all');
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

  const TEMPERATURES = [
    { value: 'chaud', label: t('hot'), color: 'bg-red-100 text-red-800 border-red-200', icon: '🔥' },
    { value: 'tiède', label: t('warm'), color: 'bg-amber-100 text-amber-800 border-amber-200', icon: '🌡️' },
    { value: 'froid', label: t('cold'), color: 'bg-slate-100 text-slate-700 border-slate-200', icon: '❄️' },
  ];

  const SITUATIONS = ['Célibataire', 'Marié(e)', 'Divorcé(e)', 'Veuf/Veuve', 'En couple'];

  const [formData, setFormData] = useState({
    nom: '',
    telephone: '',
    email: '',
    salaire: '',
    situation_familiale: '',
    notes: '',
    statut: 'nouveau',
    temperature: 'froid',
    appartement_id: '',
  });

  const fetchData = async () => {
    try {
      const [clientsRes, appartsRes] = await Promise.all([
        axios.get(`${API}/clients`, { withCredentials: true }),
        axios.get(`${API}/appartements`, { withCredentials: true }),
      ]);
      setClients(clientsRes.data);
      setAppartements(appartsRes.data);
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
    if (lastMessage?.type?.includes('client') || lastMessage?.type?.includes('appartement') || lastMessage?.type === 'new_lead') {
      fetchData();
    }
  }, [lastMessage]);

  const resetForm = () => {
    setFormData({
      nom: '',
      telephone: '',
      email: '',
      salaire: '',
      situation_familiale: '',
      notes: '',
      statut: 'nouveau',
      temperature: 'froid',
      appartement_id: '',
    });
    setEditingClient(null);
  };

  const openDialog = (client = null) => {
    if (client) {
      setEditingClient(client);
      setFormData({
        nom: client.nom || '',
        telephone: client.telephone || '',
        email: client.email || '',
        salaire: client.salaire?.toString() || '',
        situation_familiale: client.situation_familiale || '',
        notes: client.notes || '',
        statut: client.statut || 'nouveau',
        temperature: client.temperature || 'froid',
        appartement_id: client.appartement_id || '',
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
      salaire: formData.salaire ? parseFloat(formData.salaire) : null,
      appartement_id: formData.appartement_id && formData.appartement_id !== 'none' ? formData.appartement_id : null,
      situation_familiale: formData.situation_familiale && formData.situation_familiale !== 'none' ? formData.situation_familiale : null,
    };

    try {
      if (editingClient) {
        await axios.put(`${API}/clients/${editingClient.id}`, payload, { withCredentials: true });
        toast.success(t('success'));
      } else {
        await axios.post(`${API}/clients`, payload, { withCredentials: true });
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

  const handleDelete = async (clientId) => {
    if (!window.confirm(t('confirm') + '?')) return;

    try {
      await axios.delete(`${API}/clients/${clientId}`, { withCredentials: true });
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(t('error'));
    }
  };

  const handleExportExcel = () => {
    window.open(`${API}/export/clients/excel`, '_blank');
  };

  const handleExportPDF = () => {
    window.open(`${API}/export/clients/pdf`, '_blank');
  };

  const filteredClients = clients.filter((client) => {
    const matchesSearch =
      client.nom?.toLowerCase().includes(search.toLowerCase()) ||
      client.telephone?.includes(search) ||
      client.email?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || client.statut === statusFilter;
    const matchesTemp = tempFilter === 'all' || client.temperature === tempFilter;
    return matchesSearch && matchesStatus && matchesTemp;
  });

  const getStatusBadge = (statut) => {
    const status = CLIENT_STATUSES.find((s) => s.value === statut);
    return status ? (
      <Badge className={`${status.color} border`}>{status.label}</Badge>
    ) : (
      <Badge>{statut}</Badge>
    );
  };

  const getTempBadge = (temp) => {
    const temperature = TEMPERATURES.find((t) => t.value === temp);
    return temperature ? (
      <Badge className={`${temperature.color} border`}>
        {temperature.icon} {temperature.label}
      </Badge>
    ) : (
      <Badge>{temp}</Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" />
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in" data-testid="clients-page">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
            {t('clients')}
          </h1>
          <p className="text-slate-500 mt-1">{clients.length} {t('clients').toLowerCase()}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportExcel} data-testid="export-excel">
            <FileSpreadsheet className="h-4 w-4 me-2" />
            Excel
          </Button>
          <Button variant="outline" onClick={handleExportPDF} data-testid="export-pdf">
            <FileText className="h-4 w-4 me-2" />
            PDF
          </Button>
          <Button onClick={() => openDialog()} className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" data-testid="add-client-btn">
            <Plus className="h-4 w-4 me-2" />
            {t('addClient')}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder={t('search')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="ps-10"
            data-testid="search-clients"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48" data-testid="filter-status">
            <SelectValue placeholder={t('filterByStatus')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allStatuses')}</SelectItem>
            {CLIENT_STATUSES.map((status) => (
              <SelectItem key={status.value} value={status.value}>
                {status.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={tempFilter} onValueChange={setTempFilter}>
          <SelectTrigger className="w-48" data-testid="filter-temp">
            <SelectValue placeholder={t('temperature')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t('allStatuses')}</SelectItem>
            {TEMPERATURES.map((temp) => (
              <SelectItem key={temp.value} value={temp.value}>
                {temp.icon} {temp.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="bg-white rounded border border-slate-200">
        <Table className="table-luxury">
          <TableHeader>
            <TableRow>
              <TableHead>{t('name')}</TableHead>
              <TableHead>{t('phone')}</TableHead>
              <TableHead>{t('email')}</TableHead>
              <TableHead>{t('status')}</TableHead>
              <TableHead>{t('temperature')}</TableHead>
              <TableHead>Source</TableHead>
              <TableHead className="text-end">{t('actions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredClients.length > 0 ? (
              filteredClients.map((client) => (
                <TableRow key={client.id} data-testid={`client-row-${client.id}`}>
                  <TableCell className="font-medium">{client.nom}</TableCell>
                  <TableCell>{client.telephone}</TableCell>
                  <TableCell>{client.email || '-'}</TableCell>
                  <TableCell>{getStatusBadge(client.statut)}</TableCell>
                  <TableCell>{getTempBadge(client.temperature)}</TableCell>
                  <TableCell>
                    {client.source === 'whatsapp' ? (
                      <Badge className="bg-green-100 text-green-800 border border-green-200">
                        <MessageSquare className="h-3 w-3 me-1" />
                        WhatsApp
                      </Badge>
                    ) : (
                      <Badge variant="outline">Manual</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-end">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openDialog(client)}
                        data-testid={`edit-client-${client.id}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-red-500 hover:text-red-700"
                        onClick={() => handleDelete(client.id)}
                        data-testid={`delete-client-${client.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                  {t('noClients')}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F]">
              {editingClient ? t('editClient') : t('addClient')}
            </DialogTitle>
            <DialogDescription>
              {editingClient ? t('edit') : t('create')}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nom">{t('name')} *</Label>
                <Input
                  id="nom"
                  value={formData.nom}
                  onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                  required
                  data-testid="client-nom"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telephone">{t('phone')} *</Label>
                <Input
                  id="telephone"
                  value={formData.telephone}
                  onChange={(e) => setFormData({ ...formData, telephone: e.target.value })}
                  required
                  data-testid="client-telephone"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">{t('email')}</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                data-testid="client-email"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="statut">{t('status')} *</Label>
                <Select
                  value={formData.statut}
                  onValueChange={(v) => setFormData({ ...formData, statut: v })}
                >
                  <SelectTrigger data-testid="client-statut">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CLIENT_STATUSES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="temperature">{t('temperature')} *</Label>
                <Select
                  value={formData.temperature}
                  onValueChange={(v) => setFormData({ ...formData, temperature: v })}
                >
                  <SelectTrigger data-testid="client-temperature">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TEMPERATURES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.icon} {t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="salaire">{t('salary')} (DA)</Label>
                <Input
                  id="salaire"
                  type="number"
                  value={formData.salaire}
                  onChange={(e) => setFormData({ ...formData, salaire: e.target.value })}
                  data-testid="client-salaire"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="situation">{t('situation')}</Label>
                <Select
                  value={formData.situation_familiale}
                  onValueChange={(v) => setFormData({ ...formData, situation_familiale: v })}
                >
                  <SelectTrigger data-testid="client-situation">
                    <SelectValue placeholder={t('none')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">{t('none')}</SelectItem>
                    {SITUATIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="appartement">{t('apartment')}</Label>
              <Select
                value={formData.appartement_id}
                onValueChange={(v) => setFormData({ ...formData, appartement_id: v })}
              >
                <SelectTrigger data-testid="client-appartement">
                  <SelectValue placeholder={t('none')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">{t('none')}</SelectItem>
                  {appartements.filter(a => a.statut === 'disponible' || a.id === formData.appartement_id).map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.type_appart} - {t('floor')} {a.etage} ({a.prix?.toLocaleString('fr-FR')} DA)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">{t('notes')}</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
                data-testid="client-notes"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                {t('cancel')}
              </Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-client-btn">
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
