import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Badge } from '../components/ui/badge';
import { MessageSquare, Send, Bot, User, Loader2, Phone } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function WhatsApp() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testPhone, setTestPhone] = useState('+33612345678');
  const [testMessage, setTestMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [testResponse, setTestResponse] = useState(null);
  const scrollRef = useRef(null);

  const fetchConversations = async () => {
    try {
      const { data } = await axios.get(`${API}/whatsapp/conversations`, { withCredentials: true });
      setConversations(data);
    } catch (e) {
      console.error('Error fetching conversations:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  const handleTestMessage = async (e) => {
    e.preventDefault();
    if (!testMessage.trim()) return;

    setSending(true);
    setTestResponse(null);

    try {
      const { data } = await axios.post(
        `${API}/whatsapp/message`,
        { phone: testPhone, message: testMessage },
        { withCredentials: true }
      );
      setTestResponse(data.response);
      setTestMessage('');
      fetchConversations();
      toast.success('Message envoyé et traité par l\'IA');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de l\'envoi');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 fade-in" data-testid="whatsapp-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 font-['Outfit']">
          IA WhatsApp
        </h1>
        <p className="text-slate-500 mt-1">Agent IA automatique pour répondre aux clients</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Interface */}
        <Card data-testid="test-chat-card">
          <CardHeader>
            <CardTitle className="text-lg font-semibold font-['Outfit'] flex items-center gap-2">
              <Bot className="h-5 w-5 text-green-500" />
              Tester l'agent IA
            </CardTitle>
            <CardDescription>
              Simulez une conversation WhatsApp pour tester les réponses de l'IA
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Simulated Chat */}
            <div className="bg-slate-50 rounded-lg p-4 min-h-[200px] max-h-[300px] overflow-y-auto" ref={scrollRef}>
              {testResponse ? (
                <div className="space-y-3">
                  <div className="flex gap-2 justify-end">
                    <div className="bg-green-500 text-white rounded-lg px-4 py-2 max-w-[80%]">
                      <p className="text-sm">{testMessage || 'Message envoyé'}</p>
                    </div>
                    <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-green-600" />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-blue-600" />
                    </div>
                    <div className="bg-white border border-slate-200 rounded-lg px-4 py-2 max-w-[80%]">
                      <p className="text-sm text-slate-700">{testResponse}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-slate-400">
                  <p className="text-sm">Envoyez un message pour tester l'agent</p>
                </div>
              )}
            </div>

            {/* Test Form */}
            <form onSubmit={handleTestMessage} className="space-y-3">
              <div className="flex gap-2">
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-100 rounded-md text-sm text-slate-600">
                  <Phone className="h-4 w-4" />
                  <Input
                    value={testPhone}
                    onChange={(e) => setTestPhone(e.target.value)}
                    className="w-32 h-6 text-xs border-0 bg-transparent p-0"
                    placeholder="+33..."
                    data-testid="test-phone"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Input
                  value={testMessage}
                  onChange={(e) => setTestMessage(e.target.value)}
                  placeholder="Tapez un message..."
                  className="flex-1"
                  data-testid="test-message"
                />
                <Button 
                  type="submit" 
                  className="bg-green-500 hover:bg-green-600"
                  disabled={sending || !testMessage.trim()}
                  data-testid="send-test-btn"
                >
                  {sending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* AI Status */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold font-['Outfit'] flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-green-500" />
              Configuration IA
            </CardTitle>
            <CardDescription>
              Paramètres de l'agent automatique
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-3">
                <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse"></div>
                <span className="font-medium text-green-700">Agent actif</span>
              </div>
              <Badge className="bg-green-100 text-green-800">GPT-5.2</Badge>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Modèle</span>
                <span className="font-medium">OpenAI GPT-5.2</span>
              </div>
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Langue</span>
                <span className="font-medium">Français</span>
              </div>
              <div className="flex justify-between p-3 bg-slate-50 rounded-lg">
                <span className="text-slate-600">Mode</span>
                <span className="font-medium">Assistant immobilier</span>
              </div>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-700">
                <strong>Fonctionnalités:</strong>
              </p>
              <ul className="text-sm text-blue-600 mt-2 space-y-1 list-disc list-inside">
                <li>Répond aux questions sur les appartements</li>
                <li>Qualifie les prospects (budget, type recherché)</li>
                <li>Collecte les informations de contact</li>
                <li>Enregistre les leads dans le CRM</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Conversations History */}
      <Card data-testid="conversations-history">
        <CardHeader>
          <CardTitle className="text-lg font-semibold font-['Outfit']">
            Historique des conversations
          </CardTitle>
          <CardDescription>
            Dernières interactions avec l'agent IA
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            </div>
          ) : conversations.length > 0 ? (
            <ScrollArea className="h-[400px]">
              <div className="space-y-4">
                {conversations.map((conv) => (
                  <div key={conv.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200" data-testid={`conversation-${conv.id}`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-700">{conv.phone}</span>
                      </div>
                      <span className="text-xs text-slate-400">
                        {new Date(conv.created_at).toLocaleString('fr-FR')}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <User className="h-4 w-4 text-green-500 flex-shrink-0 mt-1" />
                        <p className="text-sm text-slate-600">{conv.user_message}</p>
                      </div>
                      <div className="flex gap-2">
                        <Bot className="h-4 w-4 text-blue-500 flex-shrink-0 mt-1" />
                        <p className="text-sm text-slate-700">{conv.ai_response}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>Aucune conversation enregistrée</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
