# DJERBA CONSTRUCTION - CRM EDIMCO

## Problème Original
CRM interne pour une entreprise immobilière en Algérie (DJERBA CONSTRUCTION) pour gérer les clients et les appartements du projet EDIMCO (Résidence DJERBA).

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Auth**: JWT via localStorage (compatible iPad/Safari)
- **Design**: Luxury (Navy Blue #1E3A5F / Red #C41E3A / White)
- **i18n**: FR, EN, AR (RTL)
- **Temps réel**: WebSockets

## Fonctionnalités Implémentées

### Phase 1 - Core (DONE)
- [x] Authentification JWT (localStorage)
- [x] Gestion des clients (CRUD, statuts, température)
- [x] Gestion des résidences
- [x] Gestion des appartements (CRUD avec filtres)
- [x] Tableau de bord avec stats
- [x] Synchronisation temps réel (WebSockets)
- [x] Interface multilingue (FR/EN/AR + RTL)
- [x] Design luxe avec logo personnalisé

### Phase 2 - EDIMCO Data (DONE - 04/04/2026)
- [x] Extraction des données de 9 PDFs techniques
- [x] Peuplement de la base: 298 lots (264 logements + 8 commerces + 25 services + 1 parking + 1 crèche)
- [x] 8 bâtiments (A-H), R+11, Duplex 10e-11e étage
- [x] Prix calculé: 90,000 DA/m² TTC
- [x] Interface tableau avec filtres (bloc, type, destination, recherche par lot)
- [x] Pagination (30 lots/page)
- [x] Stats par bloc sur le tableau de bord
- [x] Export Excel mis à jour

### Phase 3 - Intégrations (EN COURS)
- [x] Code WhatsApp Meta Business API (webhook + IA GPT-5.2)
- [x] Code Resend email notifications
- [ ] Test end-to-end WhatsApp (requiert clés Meta)
- [ ] Test end-to-end Resend (requiert clé Resend)

## Données EDIMCO
| Bloc | Logements | Types |
|------|-----------|-------|
| A | 28 | F2, F3, F4, F4 Duplex |
| B | 28 | F2, F3, F4, F4 Duplex |
| C | 48 | F3, F4, F2, F5 Duplex |
| D | 28 | F2, F3, F4, F4 Duplex |
| E | 28 | F2, F3, F4, F4 Duplex |
| F | 48 | F3, F2, F4, F5 Duplex |
| G | 28 | F2, F3, F4, F4 Duplex |
| H | 28 | F2, F3, F4, F4 Duplex |
| **Total** | **264** | |
+ 8 commerces + 25 services + 1 parking (location) + 1 crèche

## Backlog
- P0: Attendre les fichiers supplémentaires de l'utilisateur (plans bâtiments A-F détaillés)
- P1: Vérification WhatsApp Meta webhook end-to-end
- P2: Vérification exports PDF/Excel
- P3: Refactoring server.py si nécessaire

## Intégrations Tierces
- Meta WhatsApp Business Cloud API (requiert clé utilisateur)
- Resend (requiert clé utilisateur)
- OpenAI GPT-5.2 via Emergent LLM Key (pour IA WhatsApp)

## Schéma DB
- `users`: {email, hashed_password, role, name}
- `clients`: {nom, telephone, email, salaire, situation_familiale, notes, statut, temperature, source}
- `residences`: {nom, adresse, description}
- `appartements`: {residence_id, numero_lot, bloc, type_appart, prix, etage, statut, surface, surface_habitable, surface_utile, description, destination, client_id}
- `chatmessages`: {client_id, direction, content, timestamp}
