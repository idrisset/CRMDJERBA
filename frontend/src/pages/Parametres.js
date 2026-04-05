import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Plus, Pencil, Trash2, Building2, Loader2, Users, Bell, Mail, X } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function Parametres() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [residences, setResidences] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingResidence, setEditingResidence] = useState(null);
  const [saving, setSaving] = useState(false);

  // Notification settings
  const [notifSettings, setNotifSettings] = useState({
    email_enabled: false,
    notification_emails: []
  });
  const [newEmail, setNewEmail] = useState('');
  const [savingNotif, setSavingNotif] = useState(false);

  const [formData, setFormData] = useState({
    nom: '',
    adresse: '',
    description: '',
  });

  const fetchData = async () => {
    try {
      const [residencesRes, usersRes, notifRes] = await Promise.all([
        axios.get(`${API}/residences`),
        axios.get(`${API}/users`),
        axios.get(`${API}/settings/notifications`),
      ]);
      setResidences(residencesRes.data);
      setUsers(usersRes.data);
      setNotifSettings(notifRes.data);
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
        await axios.put(`${API}/residences/${editingResidence.id}`, formData);
        toast.success(t('success'));
      } else {
        await axios.post(`${API}/residences`, formData);
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

  const handleDelete = async (residenceId) => {
    if (!window.confirm(t('confirm') + '?')) return;

    try {
      await axios.delete(`${API}/residences/${residenceId}`);
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    }
  };

  const handleAddEmail = () => {
    if (newEmail && !notifSettings.notification_emails.includes(newEmail)) {
      setNotifSettings({
        ...notifSettings,
        notification_emails: [...notifSettings.notification_emails, newEmail]
      });
      setNewEmail('');
    }
  };

  const handleRemoveEmail = (email) => {
    setNotifSettings({
      ...notifSettings,
      notification_emails: notifSettings.notification_emails.filter(e => e !== email)
    });
  };

  const handleSaveNotifications = async () => {
    setSavingNotif(true);
    try {
      await axios.put(`${API}/settings/notifications`, notifSettings);
      toast.success(t('success'));
    } catch (e) {
      toast.error(t('error'));
    } finally {
      setSavingNotif(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">{t('admin')} only</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" />
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in" data-testid="parametres-page">
      <div>
        <h1 className="text-3xl md:text-4xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
          {t('settings')}
        </h1>
        <p className="text-slate-500 mt-1">{t('admin')}</p>
      </div>

      {/* Residences Section */}
      <Card className="card-luxury">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-xl font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              {t('residences')}
            </CardTitle>
            <CardDescription>Gérez les résidences de votre portefeuille</CardDescription>
          </div>
          <Button onClick={() => openDialog()} className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" data-testid="add-residence-btn">
            <Plus className="h-4 w-4 me-2" />
            {t('addResidence')}
          </Button>
        </CardHeader>
        <CardContent>
          {residences.length > 0 ? (
            <div className="space-y-4">
              {residences.map((residence) => (
                <div
                  key={residence.id}
                  className="flex items-center justify-between p-4 rounded bg-slate-50 border border-slate-200"
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
            <p className="text-center py-8 text-slate-500">{t('noApartments')}</p>
          )}
        </CardContent>
      </Card>

      {/* Notifications Section */}
      <Card className="card-luxury">
        <CardHeader>
          <CardTitle className="text-xl font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
            <Bell className="h-5 w-5" />
            {t('notifications')}
          </CardTitle>
          <CardDescription>{t('emailNotifications')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded border border-slate-200">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-slate-400" />
              <div>
                <p className="font-medium text-slate-900">{t('emailNotifications')}</p>
                <p className="text-sm text-slate-500">Recevoir des alertes pour les nouveaux leads</p>
              </div>
            </div>
            <Switch
              checked={notifSettings.email_enabled}
              onCheckedChange={(checked) => setNotifSettings({ ...notifSettings, email_enabled: checked })}
              data-testid="email-notifications-switch"
            />
          </div>

          {notifSettings.email_enabled && (
            <div className="space-y-4">
              <Label>{t('notificationEmails')}</Label>
              <div className="flex gap-2">
                <Input
                  type="email"
                  placeholder="email@exemple.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  data-testid="new-notification-email"
                />
                <Button onClick={handleAddEmail} variant="outline" data-testid="add-email-btn">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="flex flex-wrap gap-2">
                {notifSettings.notification_emails.map((email) => (
                  <div 
                    key={email} 
                    className="flex items-center gap-2 bg-slate-100 px-3 py-1 rounded-full text-sm"
                  >
                    <span>{email}</span>
                    <button 
                      onClick={() => handleRemoveEmail(email)}
                      className="text-slate-400 hover:text-red-500"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>

              <Button 
                onClick={handleSaveNotifications} 
                className="bg-[#1E3A5F] hover:bg-[#2A4D7C]"
                disabled={savingNotif}
                data-testid="save-notifications-btn"
              >
                {savingNotif ? <Loader2 className="h-4 w-4 animate-spin me-2" /> : null}
                {t('save')}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Users Section */}
      <Card className="card-luxury">
        <CardHeader>
          <CardTitle className="text-xl font-medium text-[#1E3A5F] font-['Outfit'] flex items-center gap-2">
            <Users className="h-5 w-5" />
            {t('users')}
          </CardTitle>
          <CardDescription>Liste des commerciaux et administrateurs</CardDescription>
        </CardHeader>
        <CardContent>
          {users.length > 0 ? (
            <div className="space-y-3">
              {users.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center justify-between p-4 rounded bg-slate-50 border border-slate-200"
                  data-testid={`user-item-${u.id}`}
                >
                  <div>
                    <p className="font-medium text-slate-900">{u.name}</p>
                    <p className="text-sm text-slate-500">{u.email}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    u.role === 'admin' ? 'bg-[#1E3A5F] text-white' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {u.role === 'admin' ? t('admin') : t('commercial')}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-8 text-slate-500">{t('noClients')}</p>
          )}
        </CardContent>
      </Card>

      {/* Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F]">
              {editingResidence ? t('editResidence') : t('addResidence')}
            </DialogTitle>
            <DialogDescription>
              {editingResidence ? t('edit') : t('create')}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="nom">{t('name')} *</Label>
              <Input
                id="nom"
                value={formData.nom}
                onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                required
                data-testid="residence-nom"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="adresse">{t('address')}</Label>
              <Input
                id="adresse"
                value={formData.adresse}
                onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
                data-testid="residence-adresse"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">{t('description')}</Label>
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
                {t('cancel')}
              </Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-residence-btn">
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
