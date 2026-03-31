import { useState, useEffect } from 'react';
import axios from 'axios';
import { useWebSocket } from '../contexts/WebSocketContext';
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
import { Plus, Pencil, Trash2, Building2, Loader2, Home } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const APPART_TYPES = ['F1', 'F2', 'F3', 'F4', 'F5', 'Studio', 'Duplex'];
const APPART_STATUSES = [
  { value: 'disponible', label: 'Disponible', color: 'bg-emerald-100 text-emerald-800' },
  { value: 'réservé', label: 'Réservé', color: 'bg-amber-100 text-amber-800' },
  { value: 'vendu', label: 'Vendu', color: 'bg-slate-200 text-slate-700' },
];

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
      toast.error('Erreur lors du chargement des données');
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
        toast.success('Appartement mis à jour');
      } else {
        await axios.post(`${API}/appartements`, payload, { withCredentials: true });
        toast.success('Appartement créé');
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

  const handleDelete = async (appartId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet appartement ?')) return;

    try {
      await axios.delete(`${API}/appartements/${appartId}`, { withCredentials: true });
      toast.success('Appartement supprimé');
      fetchData();
    } catch (e) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const getStatusBadge = (statut) => {
    const status = APPART_STATUSES.find((s) => s.value === statut);
    return status ? (
      <Badge className={status.color}>{status.label}</Badge>
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
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in" data-testid="appartements-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-['Outfit']">
            Appartements
          </h1>
          <p className="text-slate-500 mt-1">Gérez vos appartements par résidence</p>
        </div>
        <Button onClick={() => openDialog()} className="bg-blue-600 hover:bg-blue-700" data-testid="add-appart-btn">
          <Plus className="h-4 w-4 mr-2" />
          Ajouter un appartement
        </Button>
      </div>

      {/* Residence Tabs */}
      {residences.length > 0 ? (
        <Tabs value={selectedResidence} onValueChange={setSelectedResidence}>
          <TabsList className="bg-white border border-slate-200">
            {residences.map((residence) => (
              <TabsTrigger
                key={residence.id}
                value={residence.id}
                className="data-[state=active]:bg-blue-50 data-[state=active]:text-blue-600"
                data-testid={`tab-${residence.nom.toLowerCase().replace(/\s/g, '-')}`}
              >
                <Building2 className="h-4 w-4 mr-2" />
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
                        <p className="text-sm text-emerald-600">Disponibles</p>
                        <p className="text-2xl font-bold text-emerald-700">
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
                        <p className="text-sm text-amber-600">Réservés</p>
                        <p className="text-2xl font-bold text-amber-700">
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
                        <p className="text-sm text-slate-600">Vendus</p>
                        <p className="text-2xl font-bold text-slate-700">
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
                    <Card key={appart.id} className="hover:shadow-md transition-shadow" data-testid={`appart-card-${appart.id}`}>
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg font-semibold font-['Outfit']">
                            {appart.type_appart}
                          </CardTitle>
                          {getStatusBadge(appart.statut)}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Prix</span>
                            <span className="font-medium">{appart.prix?.toLocaleString('fr-FR')} €</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Étage</span>
                            <span className="font-medium">{appart.etage}</span>
                          </div>
                          {appart.surface && (
                            <div className="flex justify-between">
                              <span className="text-slate-500">Surface</span>
                              <span className="font-medium">{appart.surface} m²</span>
                            </div>
                          )}
                          {appart.client_id && (
                            <div className="flex justify-between">
                              <span className="text-slate-500">Client</span>
                              <span className="font-medium text-blue-600">{getClientName(appart.client_id)}</span>
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
                            <Pencil className="h-3 w-3 mr-1" />
                            Modifier
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
                    <p>Aucun appartement dans cette résidence</p>
                    <Button onClick={() => openDialog()} className="mt-4" variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Ajouter un appartement
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
            <p>Aucune résidence configurée</p>
            <p className="text-sm mt-1">Allez dans Paramètres pour créer des résidences</p>
          </CardContent>
        </Card>
      )}

      {/* Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-['Outfit']">
              {editingAppart ? 'Modifier l\'appartement' : 'Ajouter un appartement'}
            </DialogTitle>
            <DialogDescription>
              {editingAppart ? 'Modifiez les informations de l\'appartement' : 'Remplissez les informations du nouvel appartement'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="residence">Résidence *</Label>
                <Select
                  value={formData.residence_id}
                  onValueChange={(v) => setFormData({ ...formData, residence_id: v })}
                >
                  <SelectTrigger data-testid="appart-residence">
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    {residences.map((r) => (
                      <SelectItem key={r.id} value={r.id}>{r.nom}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Type *</Label>
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
                <Label htmlFor="prix">Prix (€) *</Label>
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
                <Label htmlFor="etage">Étage *</Label>
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
                <Label htmlFor="surface">Surface (m²)</Label>
                <Input
                  id="surface"
                  type="number"
                  value={formData.surface}
                  onChange={(e) => setFormData({ ...formData, surface: e.target.value })}
                  data-testid="appart-surface"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="statut">Statut *</Label>
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
                <Label htmlFor="client">Client lié</Label>
                <Select
                  value={formData.client_id}
                  onValueChange={(v) => setFormData({ ...formData, client_id: v })}
                >
                  <SelectTrigger data-testid="appart-client">
                    <SelectValue placeholder="Sélectionner un client" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Aucun</SelectItem>
                    {clients.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.nom} - {c.telephone}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
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
                Annuler
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={saving} data-testid="save-appart-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {editingAppart ? 'Enregistrer' : 'Créer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
