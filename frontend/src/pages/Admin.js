import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ShieldCheck, UserPlus, Check, X, Clock, Loader2, Users, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

const ROLE_OPTIONS = [
  { value: 'super_admin', label: 'Super Administrateur', color: 'bg-red-100 text-red-800 border-red-200' },
  { value: 'admin_limited', label: 'Administrateur Limité', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  { value: 'user', label: 'Utilisateur', color: 'bg-blue-100 text-blue-800 border-blue-200' },
];

export function Admin() {
  const { user } = useAuth();
  const { lastMessage } = useWebSocket();
  const { t } = useLanguage();
  const [users, setUsers] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isUserDialogOpen, setIsUserDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [userForm, setUserForm] = useState({ name: '', email: '', password: '', role: 'user' });

  const isSuperAdmin = user?.permissions?.level >= 3 || user?.role === 'super_admin' || user?.role === 'admin';

  const fetchData = async () => {
    try {
      const [usersRes, approvalsRes] = await Promise.all([
        axios.get(`${API}/users`),
        axios.get(`${API}/approvals`),
      ]);
      setUsers(usersRes.data || []);
      setApprovals(approvalsRes.data || []);
    } catch (e) {
      console.error('Admin fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => {
    if (lastMessage?.type?.includes('approval')) fetchData();
  }, [lastMessage]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.post(`${API}/users`, userForm);
      toast.success(t('success'));
      setIsUserDialogOpen(false);
      setUserForm({ name: '', email: '', password: '', role: 'user' });
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    } finally {
      setSaving(false);
    }
  };

  const handleApproval = async (id, decision) => {
    try {
      await axios.post(`${API}/approvals/${id}/${decision}`);
      toast.success(decision === 'approve' ? t('approved') : t('rejected'));
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    }
  };

  const handleDeactivate = async (userId) => {
    if (!window.confirm('Désactiver cet utilisateur ?')) return;
    try {
      await axios.delete(`${API}/users/${userId}`);
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await axios.put(`${API}/users/${userId}`, { role: newRole });
      toast.success(t('success'));
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || t('error'));
    }
  };

  const getRoleBadge = (role) => {
    const r = ROLE_OPTIONS.find(x => x.value === role) || ROLE_OPTIONS.find(x => x.value === 'user');
    return <Badge className={`${r.color} border text-xs`}>{r.label}</Badge>;
  };

  const getActionLabel = (action) => {
    const labels = {
      delete_client: 'Suppression client',
      delete_appartement: 'Suppression appartement',
      delete_prospect: 'Suppression prospect',
      modify_price: 'Modification prix',
    };
    return labels[action] || action;
  };

  const pendingApprovals = approvals.filter(a => a.status === 'pending');
  const historyApprovals = approvals.filter(a => a.status !== 'pending');

  if (!isSuperAdmin) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="admin-forbidden">
        <div className="text-center">
          <ShieldCheck className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Accès réservé au Super Administrateur</p>
        </div>
      </div>
    );
  }

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-6 fade-in" data-testid="admin-page">
      <div>
        <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
          {t('administration')}
        </h1>
        <p className="text-slate-500 mt-1">{t('userManagement')} & {t('pendingApprovals')}</p>
      </div>

      <Tabs defaultValue="users">
        <TabsList className="bg-slate-100">
          <TabsTrigger value="users" className="gap-2" data-testid="tab-users">
            <Users className="h-4 w-4" /> {t('users')} ({users.length})
          </TabsTrigger>
          <TabsTrigger value="approvals" className="gap-2" data-testid="tab-approvals">
            <Clock className="h-4 w-4" /> {t('pendingApprovals')}
            {pendingApprovals.length > 0 && (
              <Badge className="bg-red-500 text-white text-xs ms-1">{pendingApprovals.length}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="tab-history">
            {t('approvalHistory')}
          </TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users">
          <Card className="card-luxury">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit']">{t('userManagement')}</CardTitle>
              <Button size="sm" onClick={() => setIsUserDialogOpen(true)} className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" data-testid="add-user-btn">
                <UserPlus className="h-4 w-4 me-1" /> {t('addUser')}
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#1E3A5F]">
                    <TableHead className="text-white text-xs">{t('name')}</TableHead>
                    <TableHead className="text-white text-xs">{t('email')}</TableHead>
                    <TableHead className="text-white text-xs">{t('role')}</TableHead>
                    <TableHead className="text-white text-xs">{t('status')}</TableHead>
                    <TableHead className="text-white text-xs w-[120px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map(u => (
                    <TableRow key={u.id} data-testid={`user-row-${u.id}`}>
                      <TableCell className="font-medium text-sm">{u.name}</TableCell>
                      <TableCell className="text-sm text-slate-600">{u.email}</TableCell>
                      <TableCell>
                        {u.id === user?.id || u.id === user?._id ? (
                          getRoleBadge(u.role)
                        ) : (
                          <Select value={u.role} onValueChange={v => handleRoleChange(u.id, v)}>
                            <SelectTrigger className="h-8 w-48"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              {ROLE_OPTIONS.map(r => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={u.is_active !== false ? 'bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs' : 'bg-red-100 text-red-800 border border-red-200 text-xs'}>
                          {u.is_active !== false ? t('active') : t('inactive')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {u.id !== user?.id && u.id !== user?._id && u.is_active !== false && (
                          <Button variant="ghost" size="sm" className="text-red-500 text-xs h-7" onClick={() => handleDeactivate(u.id)} data-testid={`deactivate-${u.id}`}>
                            {t('deactivateUser')}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pending Approvals Tab */}
        <TabsContent value="approvals">
          <Card className="card-luxury">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit']">{t('pendingApprovals')}</CardTitle>
            </CardHeader>
            <CardContent>
              {pendingApprovals.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Check className="h-12 w-12 mx-auto mb-3 text-emerald-300" />
                  <p>{t('noApprovals')}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingApprovals.map(a => (
                    <div key={a.id} className="flex items-center justify-between p-4 rounded-lg border border-amber-200 bg-amber-50" data-testid={`approval-${a.id}`}>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <AlertTriangle className="h-4 w-4 text-amber-600" />
                          <span className="font-medium text-sm">{getActionLabel(a.action)}</span>
                        </div>
                        <p className="text-sm text-slate-700">{a.entity_name} ({a.entity_type})</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {t('requestedBy')}: <span className="font-medium">{a.requester_name}</span> - {new Date(a.created_at).toLocaleDateString('fr-FR')} {new Date(a.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                        </p>
                        {a.details && Object.keys(a.details).length > 0 && (
                          <p className="text-xs text-slate-400 mt-1">{Object.entries(a.details).map(([k, v]) => `${k}: ${v}`).join(' | ')}</p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 h-8" onClick={() => handleApproval(a.id, 'approve')} data-testid={`approve-${a.id}`}>
                          <Check className="h-3 w-3 me-1" /> {t('approve')}
                        </Button>
                        <Button size="sm" variant="outline" className="border-red-300 text-red-600 hover:bg-red-50 h-8" onClick={() => handleApproval(a.id, 'reject')} data-testid={`reject-${a.id}`}>
                          <X className="h-3 w-3 me-1" /> {t('reject')}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card className="card-luxury">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-[#1E3A5F] font-['Outfit']">{t('approvalHistory')}</CardTitle>
            </CardHeader>
            <CardContent>
              {historyApprovals.length === 0 ? (
                <p className="text-center py-8 text-slate-400">Aucun historique</p>
              ) : (
                <div className="space-y-2">
                  {historyApprovals.map(a => (
                    <div key={a.id} className="flex items-center justify-between p-3 rounded bg-slate-50 border border-slate-100">
                      <div>
                        <span className="text-sm font-medium">{getActionLabel(a.action)}</span>
                        <span className="text-xs text-slate-500 ms-2">{a.entity_name}</span>
                        <p className="text-xs text-slate-400">{a.requester_name} - {new Date(a.created_at).toLocaleDateString('fr-FR')}</p>
                      </div>
                      <div className="text-end">
                        <Badge className={a.status === 'approved' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs' : 'bg-red-100 text-red-800 border border-red-200 text-xs'}>
                          {a.status === 'approved' ? t('approved') : t('rejected')}
                        </Badge>
                        <p className="text-xs text-slate-400 mt-1">{a.reviewed_by}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create User Dialog */}
      <Dialog open={isUserDialogOpen} onOpenChange={setIsUserDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="font-['Outfit'] text-[#1E3A5F]">{t('addUser')}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div className="space-y-1">
              <Label className="text-xs">{t('name')} *</Label>
              <Input value={userForm.name} onChange={e => setUserForm({ ...userForm, name: e.target.value })} required data-testid="user-name" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">{t('email')} *</Label>
              <Input type="email" value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })} required data-testid="user-email" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">{t('password')} *</Label>
              <Input type="password" value={userForm.password} onChange={e => setUserForm({ ...userForm, password: e.target.value })} required minLength={6} data-testid="user-password" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">{t('role')}</Label>
              <Select value={userForm.role} onValueChange={v => setUserForm({ ...userForm, role: v })}>
                <SelectTrigger data-testid="user-role"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {ROLE_OPTIONS.map(r => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsUserDialogOpen(false)}>{t('cancel')}</Button>
              <Button type="submit" className="bg-[#1E3A5F] hover:bg-[#2A4D7C]" disabled={saving} data-testid="save-user-btn">
                {saving && <Loader2 className="h-4 w-4 animate-spin me-2" />} {t('save')}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
