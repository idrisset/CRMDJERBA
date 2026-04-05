# DJERBA CONSTRUCTION - CRM EDIMCO

## Probleme Original
CRM interne pour DJERBA CONSTRUCTION (Algerie) - gestion clients et appartements du projet EDIMCO.

## Architecture
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Auth: JWT localStorage (iPad/Safari compatible)
- Design: Luxury (Navy #1E3A5F / Red #C41E3A / White)
- i18n: FR, EN, AR (RTL)
- Real-time: WebSockets

## Donnees EDIMCO (Lots 224-518)
296 lots | 264 logements | 8 commerces | 22 services | 1 parking | 1 creche
Blocs A-H, R+11, Duplex 10e-11e. Prix: 90 000 DA/m2 TTC

## Fonctionnalites
- [x] Auth JWT localStorage
- [x] EDIMCO branding (Dashboard, Clients, Appartements)
- [x] Gestion clients (CRUD, statuts, formulaire enrichi: tel2, objectif, salaire, budget min/max, mode paiement, etage souhaite)
- [x] Gestion appartements avec onglets par type (F2/F3/F4/Duplex/Commerce/Service)
- [x] Systeme de reservation: assigner un appart a un client -> auto-bloque + nom visible
- [x] Historique des reservations (qui, quoi, quand, par quel agent)
- [x] Detection de conflit (409 si appart deja reserve)
- [x] Suppression client -> libere l'appartement
- [x] Reservation depuis la fiche client avec filtre par type
- [x] Filtres par bloc + recherche par lot
- [x] Dashboard: stats par bloc A-H + historique reservations
- [x] WebSockets temps reel (sync entre commerciaux)
- [x] i18n FR/EN/AR + RTL
- [x] Export Excel (Clients + Appartements + Prospects)
- [x] Export PDF (Clients + Prospects)
- [x] WhatsApp Meta API (code en place, MOCKED - cles requises)
- [x] Resend email (code en place, MOCKED - cles requises)
- [x] **BIG DATA / PROSPECTS** - Module complet avec:
  - CRUD complet (ajouter/modifier/supprimer)
  - Formulaire enrichi: nom, tel, tel2, email, ville, quartier, type logement, etage, nb pieces, budget min/max, mode paiement, objectif, situation, source, notes
  - Analytics: top villes, top types, top zones, budget moyen, modes paiement
  - Filtres: recherche, par ville, par type de logement
  - Export Excel + PDF
  - i18n FR/EN/AR
  - WebSocket real-time sync

## Schema DB
- users: {email, hashed_password, role, name}
- clients: {nom, telephone, telephone2, email, salaire, budget_min, budget_max, objectif, mode_paiement, etage_souhaite, situation_familiale, notes, statut, appartement_id}
- residences: {nom, adresse, description}
- appartements: {residence_id, numero_lot, bloc, type_appart, prix, etage, statut, surface, surface_habitable, surface_utile, description, destination, client_id}
- reservations: {client_id, client_nom, appartement_id, bloc, numero_lot, type_appart, action, agent, date}
- prospects: {nom, telephone, telephone2, email, ville, quartier, type_logement, etage_souhaite, nombre_pieces, budget_min, budget_max, mode_paiement, objectif, situation_familiale, notes, source, created_at, created_by}
- chatmessages: {client_id, direction, content, timestamp}

## API Endpoints
### Prospects
- GET /api/prospects - Liste
- POST /api/prospects - Creation
- PUT /api/prospects/{id} - Mise a jour
- DELETE /api/prospects/{id} - Suppression
- GET /api/prospects/analytics - Analytique
- GET /api/export/prospects/excel - Export Excel
- GET /api/export/prospects/pdf - Export PDF

## Backlog
- P1: Test WhatsApp Meta end-to-end (cles Meta requises)
- P1: Test Resend email (cle API requise)
- P2: Test exports PDF
- P3: Refactoring server.py (1500+ lignes -> decoupe en modules)
