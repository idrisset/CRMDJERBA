import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
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
import { Plus, Pencil, Trash2, Search, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CLIENT_STATUSES = [
  { value: 'nouveau', label: 'Nouveau', color: 'bg-blue-100 text-blue-800' },
  { value: 'intéressé', label: 'Intéressé', color: 'bg-violet-100 text-violet-800' },
  { value: 'visite', label: 'Visite', color: 'bg-cyan-100 text-cyan-800' },
  { value: 'réservé', label: 'Réservé', color: 'bg-amber-100 text-amber-800' },
  { value: 'vendu', label: 'Vendu', color: 'bg-slate-200 text-slate-700' },
];

const SITUATIONS = [
  'Célibataire',
  'Marié(e)',
  'Divorcé(e)',
  'Veuf/Veuve',
  'En couple',
];

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

  const [formData, setFormData] = useState({
    nom: '',
    telephone: '',
    email: '',
    salaire: '',
    situation_familiale: '',
    notes: '',
    statut: 'nouveau',
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
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (lastMessage?.type?.includes('client') || lastMessage?.type?.includes('appartement')) {
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
        toast.success('Client mis à jour');
      } else {
        await axios.post(`${API}/clients`, payload, { withCredentials: true });
        toast.success('Client créé');
      }
      setIsDialogOpen(false);
      resetForm();
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (clientId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce client ?')) return;

    try {
      await axios.delete(`${API}/clients/${clientId}`, { withCredentials: true });
      toast.success('Client supprimé');
      fetchData();
    } catch (e) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const filteredClients = clients.filter((client) => {
    const matchesSearch =
      client.nom?.toLowerCase().includes(search.toLowerCase()) ||
      client.telephone?.includes(search) ||
      client.email?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || client.statut === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (statut) => {
    const status = CLIENT_STATUSES.find((s) => s.value === statut);
    return status ? (
      <Badge className={status.color}>{status.label}</Badge>
    ) : (
      <Badge>{statut}</Badge>
    );
  };

  const getAppartementName = (appartId) => {
    if (!appartId) return '-';
    const appart = appartements.find((a) => a.id === appartId);
    return appart ? `${appart.type_appart} - Étage ${appart.etage}` : '-';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in" data-testid="clients-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-['Outfit']">
            Clients
          </h1>
          <p className="text-slate-500 mt-1">Gérez vos clients et leur suivi</p>
        </div>
        <Button onClick={() => openDialog()} className="bg-blue-600 hover:bg-blue-700" data-testid="add-client-btn">
          <Plus className="h-4 w-4 mr-2" />
          Ajouter un client
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Rechercher un client..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
            data-testid="search-clients"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48" data-testid="filter-status">
            <SelectValue placeholder="Filtrer par statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            {CLIENT_STATUSES.map((status) => (
              <SelectItem key={status.value} value={status.value}>
                {status.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Téléphone</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Salaire</TableHead>
              <TableHead>Situation</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Appartement</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredClients.length > 0 ? (
              filteredClients.map((client) => (
                <TableRow key={client.id} className="table-row-hover" data-testid={`client-row-${client.id}`}>
                  <TableCell className="font-medium">{client.nom}</TableCell>
                  <TableCell>{client.telephone}</TableCell>
                  <TableCell>{client.email || '-'}</TableCell>
                  <TableCell>
                    {client.salaire ? `${client.salaire.toLocaleString('fr-FR')} €` : '-'}
                  </TableCell>
                  <TableCell>{client.situation_familiale || '-'}</TableCell>
                  <TableCell>{getStatusBadge(client.statut)}</TableCell>
                  <TableCell>{getAppartementName(client.appartement_id)}</TableCell>
                  <TableCell className="text-right">
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
                <TableCell colSpan={8} className="text-center py-8 text-slate-500">
                  Aucun client trouvé
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
            <DialogTitle className="font-['Outfit']">
              {editingClient ? 'Modifier le client' : 'Ajouter un client'}
            </DialogTitle>
            <DialogDescription>
              {editingClient ? 'Modifiez les informations du client' : 'Remplissez les informations du nouveau client'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nom">Nom *</Label>
                <Input
                  id="nom"
                  value={formData.nom}
                  onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                  required
                  data-testid="client-nom"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telephone">Téléphone *</Label>
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
              <Label htmlFor="email">Email</Label>
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
                <Label htmlFor="salaire">Salaire (€)</Label>
                <Input
                  id="salaire"
                  type="number"
                  value={formData.salaire}
                  onChange={(e) => setFormData({ ...formData, salaire: e.target.value })}
                  data-testid="client-salaire"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="situation">Situation familiale</Label>
                <Select
                  value={formData.situation_familiale}
                  onValueChange={(v) => setFormData({ ...formData, situation_familiale: v })}
                >
                  <SelectTrigger data-testid="client-situation">
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sélectionner</SelectItem>
                    {SITUATIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="statut">Statut *</Label>
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
                <Label htmlFor="appartement">Appartement lié</Label>
                <Select
                  value={formData.appartement_id}
                  onValueChange={(v) => setFormData({ ...formData, appartement_id: v })}
                >
                  <SelectTrigger data-testid="client-appartement">
                    <SelectValue placeholder="Aucun" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Aucun</SelectItem>
                    {appartements.filter(a => a.statut === 'disponible' || a.id === formData.appartement_id).map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.type_appart} - Étage {a.etage} ({a.prix?.toLocaleString('fr-FR')} €)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
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
                Annuler
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={saving} data-testid="save-client-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {editingClient ? 'Enregistrer' : 'Créer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
