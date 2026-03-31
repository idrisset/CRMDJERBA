# CRM Immobilier - Product Requirements Document

## Original Problem Statement
Application web CRM pour une entreprise immobilière. Système interne pour gérer les clients et les appartements avec:
- Gestion des clients (nom, téléphone, email, salaire, situation familiale, notes, suivi: nouveau/intéressé/visite/réservé/vendu)
- Gestion des appartements (3 résidences, type F2/F3, prix, étage, statut disponible/réservé/vendu)
- Système multi-utilisateurs avec synchronisation temps réel
- Tableau de bord avec statistiques
- Intégration WhatsApp avec IA (GPT-5.2)

## User Personas
1. **Admin** - Gère les résidences, utilisateurs, configuration système
2. **Commercial** - Gère les clients et appartements, suit les ventes

## Core Requirements
- Interface en français
- Auth JWT email/password
- Sync temps réel (WebSocket)
- IA WhatsApp avec GPT-5.2

## What's Been Implemented (2026-03-31)

### Backend (FastAPI + MongoDB)
- ✅ Auth JWT avec cookies httpOnly (login, register, logout, refresh)
- ✅ CRUD Clients avec tous les champs et statuts
- ✅ CRUD Appartements avec liaison client
- ✅ CRUD Résidences (admin only)
- ✅ Dashboard API avec statistiques
- ✅ WebSocket pour sync temps réel
- ✅ IA WhatsApp avec GPT-5.2 (emergentintegrations)
- ✅ Admin seeding automatique

### Frontend (React + Shadcn UI)
- ✅ Page Login/Register
- ✅ Dashboard avec KPIs (clients, appartements disponibles/réservés/vendus)
- ✅ Page Clients avec filtres, CRUD complet
- ✅ Page Appartements avec tabs par résidence, CRUD complet
- ✅ Page Paramètres (admin) pour gérer résidences
- ✅ Page IA WhatsApp avec test chat et historique
- ✅ Layout avec sidebar, indicateur de connexion WebSocket
- ✅ Design Swiss & High-Contrast, fonts Outfit/IBM Plex Sans

## Prioritized Backlog

### P0 (Done)
- [x] Auth système
- [x] CRUD Clients
- [x] CRUD Appartements
- [x] Dashboard stats
- [x] Sync WebSocket
- [x] IA WhatsApp

### P1 (Next)
- [ ] Intégration WhatsApp réelle (webhook Twilio/Meta)
- [ ] Export PDF/Excel des données
- [ ] Filtres avancés clients

### P2 (Future)
- [ ] Notifications push
- [ ] Historique des modifications
- [ ] Rapports de performance commerciale
- [ ] Mode sombre

## Tech Stack
- Backend: FastAPI, MongoDB (motor), JWT, bcrypt, WebSocket
- Frontend: React 19, Shadcn UI, Tailwind CSS, Axios
- AI: OpenAI GPT-5.2 via emergentintegrations
