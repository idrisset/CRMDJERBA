import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Plus, Pencil, Trash2, Building2, Loader2, Users } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function Parametres() {
  const { user } = useAuth();
  const [residences, setResidences] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingResidence, setEditingResidence] = useState(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    nom: '',
    adresse: '',
    description: '',
  });

  const fetchData = async () => {
    try {
      const [residencesRes, usersRes] = await Promise.all([
        axios.get(`${API}/residences`, { withCredentials: true }),
        axios.get(`${API}/users`, { withCredentials: true }),
      ]);
      setResidences(residencesRes.data);
      setUsers(usersRes.data);
    } catch (e) {
      console.error('Error fetching data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const resetForm = () => {
    setFormData({ nom: '', adresse: '', description: '' });
    setEditingResidence(null);
  };

  const openDialog = (residence = null) => {
    if (residence) {
      setEditingResidence(residence);
      setFormData({
        nom: residence.nom || '',
        adresse: residence.adresse || '',
        description: residence.description || '',
      });
    } else {
      resetForm();
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      if (editingResidence) {
        await axios.put(`${API}/residences/${editingResidence.id}`, formData, { withCredentials: true });
        toast.success('Résidence mise à jour');
      } else {
        await axios.post(`${API}/residences`, formData, { withCredentials: true });
        toast.success('Résidence créée');
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

  const handleDelete = async (residenceId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette résidence ?')) return;

    try {
      await axios.delete(`${API}/residences/${residenceId}`, { withCredentials: true });
      toast.success('Résidence supprimée');
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">Accès réservé aux administrateurs</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in" data-testid="parametres-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-['Outfit']">
          Paramètres
        </h1>
        <p className="text-slate-500 mt-1">Configurez les résidences et gérez les utilisateurs</p>
      </div>

      {/* Residences Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xl font-semibold font-['Outfit'] flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              Résidences
            </CardTitle>
            <CardDescription>Gérez les résidences de votre portefeuille</CardDescription>
          </div>
          <Button onClick={() => openDialog()} className="bg-blue-600 hover:bg-blue-700" data-testid="add-residence-btn">
            <Plus className="h-4 w-4 mr-2" />
            Ajouter
          </Button>
        </CardHeader>
        <CardContent>
          {residences.length > 0 ? (
            <div className="space-y-4">
              {residences.map((residence) => (
                <div
                  key={residence.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200"
                  data-testid={`residence-item-${residence.id}`}
                >
                  <div>
                    <p className="font-medium text-slate-900">{residence.nom}</p>
                    {residence.adresse && (
                      <p className="text-sm text-slate-500">{residence.adresse}</p>
                    )}
                    {residence.description && (
                      <p className="text-sm text-slate-400 mt-1">{residence.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => openDialog(residence)}
                      data-testid={`edit-residence-${residence.id}`}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      className="text-red-500 hover:text-red-700"
                      onClick={() => handleDelete(residence.id)}
                      data-testid={`delete-residence-${residence.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8 text-slate-500">Aucune résidence configurée</p>
          )}
        </CardContent>
      </Card>

      {/* Users Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-semibold font-['Outfit'] flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-600" />
            Utilisateurs
          </CardTitle>
          <CardDescription>Liste des commerciaux et administrateurs</CardDescription>
        </CardHeader>
        <CardContent>
          {users.length > 0 ? (
            <div className="space-y-3">
              {users.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-200"
                  data-testid={`user-item-${u.id}`}
                >
                  <div>
                    <p className="font-medium text-slate-900">{u.name}</p>
                    <p className="text-sm text-slate-500">{u.email}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    u.role === 'admin' ? 'bg-blue-100 text-blue-800' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {u.role === 'admin' ? 'Administrateur' : 'Commercial'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8 text-slate-500">Aucun utilisateur</p>
          )}
        </CardContent>
      </Card>

      {/* Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Outfit']">
              {editingResidence ? 'Modifier la résidence' : 'Ajouter une résidence'}
            </DialogTitle>
            <DialogDescription>
              {editingResidence ? 'Modifiez les informations de la résidence' : 'Créez une nouvelle résidence'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="nom">Nom de la résidence *</Label>
              <Input
                id="nom"
                value={formData.nom}
                onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                required
                data-testid="residence-nom"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="adresse">Adresse</Label>
              <Input
                id="adresse"
                value={formData.adresse}
                onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
                data-testid="residence-adresse"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                data-testid="residence-description"
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={saving} data-testid="save-residence-btn">
                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {editingResidence ? 'Enregistrer' : 'Créer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
