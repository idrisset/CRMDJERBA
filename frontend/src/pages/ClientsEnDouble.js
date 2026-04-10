import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Loader2, Users, GitMerge, AlertTriangle, Check } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL || ''}/api`;

export function ClientsEnDouble() {
  const { t } = useLanguage();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [merging, setMerging] = useState(null);

  const fetchDuplicates = async () => {
    try {
      const { data } = await axios.get(`${API}/clients/duplicates`);
      setGroups(data.groups || []);
    } catch (e) {
      console.error('Duplicates fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDuplicates(); }, []);

  const handleMerge = async (keepId, mergeId) => {
    if (!window.confirm('Fusionner ces deux clients ? Le client fusionné sera déplacé dans la corbeille.')) return;
    setMerging(`${keepId}-${mergeId}`);
    try {
      await axios.post(`${API}/clients/merge/${keepId}/${mergeId}`);
      toast.success('Clients fusionnés avec succès');
      fetchDuplicates();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de la fusion');
    } finally {
      setMerging(null);
    }
  };

  const reasonLabel = (reason) => {
    const labels = { tel: 'Téléphone', nom: 'Nom', email: 'Email' };
    return labels[reason] || reason;
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="h-8 w-8 animate-spin text-[#1E3A5F]" /></div>;

  return (
    <div className="space-y-6 fade-in" data-testid="duplicates-page">
      <div>
        <h1 className="text-2xl md:text-3xl font-light tracking-tight text-[#1E3A5F] font-['Outfit']">
          {t('duplicates')}
        </h1>
        <p className="text-slate-500 mt-1">{groups.length} {t('duplicateGroups')}</p>
      </div>

      {groups.length === 0 ? (
        <Card className="card-luxury">
          <CardContent className="py-16 text-center">
            <Check className="h-16 w-16 text-emerald-300 mx-auto mb-4" />
            <p className="text-lg text-slate-500">{t('noDuplicates')}</p>
            <p className="text-sm text-slate-400 mt-1">Tous les clients sont uniques</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {groups.map((group, gi) => (
            <Card key={gi} className="card-luxury border-l-4 border-l-amber-400" data-testid={`duplicate-group-${gi}`}>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-amber-800 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Doublon détecté : {reasonLabel(group.reason)} = "{group.match_value}"
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {group.clients.map((client, ci) => (
                    <div key={client.id} className="rounded-lg border border-slate-200 p-4 relative" data-testid={`dup-client-${client.id}`}>
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <span className="text-xs font-mono text-[#1E3A5F] font-bold">{client.reference || '-'}</span>
                          <h3 className="font-medium text-slate-900">{client.nom}</h3>
                        </div>
                        <Badge className="text-xs bg-slate-100 text-slate-600 border border-slate-200">{client.statut}</Badge>
                      </div>
                      <div className="text-xs space-y-1 text-slate-600">
                        <p>Tel: {client.telephone}</p>
                        {client.telephone2 && <p>Tel 2: {client.telephone2}</p>}
                        {client.email && <p>Email: {client.email}</p>}
                        {client.created_at && <p className="text-slate-400">Créé: {new Date(client.created_at).toLocaleDateString('fr-FR')}</p>}
                        {client.appartement_ids?.length > 0 && <p className="text-[#1E3A5F] font-medium">{client.appartement_ids.length} appartement(s)</p>}
                      </div>

                      {/* Merge buttons: for each client, show merge INTO other clients */}
                      {group.clients.length === 2 && ci === 0 && (
                        <div className="mt-3 flex gap-2">
                          <Button size="sm" variant="outline" className="text-xs flex-1 border-emerald-300 text-emerald-700 hover:bg-emerald-50" 
                            disabled={!!merging}
                            onClick={() => handleMerge(client.id, group.clients[1].id)}
                            data-testid={`keep-${client.id}`}>
                            {merging === `${client.id}-${group.clients[1].id}` ? <Loader2 className="h-3 w-3 animate-spin me-1" /> : <Check className="h-3 w-3 me-1" />}
                            {t('keepThis')}
                          </Button>
                        </div>
                      )}
                      {group.clients.length === 2 && ci === 1 && (
                        <div className="mt-3 flex gap-2">
                          <Button size="sm" variant="outline" className="text-xs flex-1 border-emerald-300 text-emerald-700 hover:bg-emerald-50" 
                            disabled={!!merging}
                            onClick={() => handleMerge(client.id, group.clients[0].id)}
                            data-testid={`keep-${client.id}`}>
                            {merging === `${client.id}-${group.clients[0].id}` ? <Loader2 className="h-3 w-3 animate-spin me-1" /> : <Check className="h-3 w-3 me-1" />}
                            {t('keepThis')}
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {group.clients.length > 2 && (
                  <div className="mt-3 p-3 rounded bg-amber-50 border border-amber-200 text-xs text-amber-700">
                    <GitMerge className="h-3 w-3 inline me-1" />
                    {group.clients.length} clients dans ce groupe. Fusionnez-les deux par deux.
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
