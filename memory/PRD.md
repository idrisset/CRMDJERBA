# DJERBA CONSTRUCTION - CRM Immobilier PRD

## Original Problem Statement
Système CRM automatisé complet pour entreprise immobilière en Algérie avec:
- Gestion clients avec température (chaud/tiède/froid) et statut pipeline
- Gestion appartements par résidence
- WhatsApp Business API avec IA GPT-5.2 automatique
- Notifications email aux commerciaux
- Export PDF/Excel
- Interface multilingue (FR/AR/EN) avec RTL
- Design luxe adapté au marché algérien

## Brand Identity
- **Nom**: DJERBA CONSTRUCTION
- **Couleurs**: Navy Blue (#1E3A5F), Red (#C41E3A), White
- **Numéro WhatsApp**: +213 770 481 500

## User Personas
1. **Admin** - Gère résidences, utilisateurs, notifications, configuration
2. **Commercial** - Gère clients, appartements, répond aux leads

## What's Been Implemented (2026-03-31)

### Backend (FastAPI + MongoDB)
- ✅ Auth JWT avec cookies httpOnly
- ✅ CRUD Clients avec température (chaud/tiède/froid) et source (manual/whatsapp)
- ✅ CRUD Appartements avec liaison client
- ✅ CRUD Résidences (admin only)
- ✅ Dashboard API avec KPIs complets
- ✅ WebSocket pour sync temps réel
- ✅ Meta WhatsApp Business API webhook (vérifié, prêt pour production)
- ✅ IA WhatsApp avec GPT-5.2 (emergentintegrations)
- ✅ Auto-création leads depuis WhatsApp
- ✅ Notifications email (Resend) aux commerciaux
- ✅ Export Excel (openpyxl)
- ✅ Export PDF (reportlab)
- ✅ Admin seeding automatique

### Frontend (React + Shadcn UI + Tailwind)
- ✅ Design luxe Navy/Red/White
- ✅ Multilingue FR/AR/EN avec RTL
- ✅ Logo SVG DJERBA CONSTRUCTION
- ✅ Page Login/Register avec background gradient
- ✅ Dashboard avec tous les KPIs (leads chauds, WhatsApp leads)
- ✅ Page Clients avec température, filtres, export
- ✅ Page Appartements avec tabs par résidence
- ✅ Page WhatsApp avec test chat et historique
- ✅ Page Paramètres (notifications email, résidences, utilisateurs)
- ✅ Layout avec sidebar Navy, indicateur WebSocket
- ✅ Language switcher dans header

## Configuration Required (Production)
```env
WHATSAPP_PHONE_NUMBER_ID=<from Meta Developer Console>
META_ACCESS_TOKEN=<from Meta Developer Console>
META_APP_SECRET=<for webhook signature verification>
RESEND_API_KEY=<from Resend dashboard>
SENDER_EMAIL=notifications@djerba-construction.com
```

## Webhook URL for Meta
`https://property-hub-612.preview.emergentagent.com/api/whatsapp/webhook`
Verify Token: `djerba_construction_whatsapp_verify_2024`

## Prioritized Backlog

### P0 (Done)
- [x] Auth système complet
- [x] CRUD Clients avec température
- [x] CRUD Appartements
- [x] Dashboard KPIs
- [x] WebSocket sync
- [x] IA WhatsApp GPT-5.2
- [x] Multilingue FR/AR/EN + RTL
- [x] Export PDF/Excel
- [x] Design luxe DJERBA

### P1 (Production Ready)
- [ ] Configurer Meta Business WhatsApp tokens
- [ ] Configurer Resend API key
- [ ] Ajouter domaine email personnalisé

### P2 (Future)
- [ ] Rapports de performance commerciale
- [ ] Historique des modifications
- [ ] Mode sombre
- [ ] App mobile

## Tech Stack
- Backend: FastAPI, MongoDB, JWT, bcrypt, WebSocket, Resend
- Frontend: React 19, Shadcn UI, Tailwind CSS, Axios
- AI: OpenAI GPT-5.2 via emergentintegrations
- WhatsApp: Meta Business Cloud API
- Email: Resend
