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
- API: Same-origin relative URLs (no cross-origin)

## Donnees EDIMCO (Lots 224-518)
296 lots | 264 logements | 8 commerces | 22 services | 1 parking | 1 creche
Blocs A-H, R+11, Duplex 10e-11e. Prix: 90 000 DA/m2 TTC

## Fonctionnalites
- [x] Auth JWT localStorage
- [x] EDIMCO branding (Dashboard, Clients, Appartements)
- [x] Gestion clients (CRUD, statuts, formulaire enrichi)
- [x] Gestion appartements avec onglets par type
- [x] Systeme de reservation
- [x] Historique des reservations
- [x] Detection de conflit (409 si appart deja reserve)
- [x] Suppression client -> libere l'appartement
- [x] Dashboard: stats par bloc A-H + historique reservations
- [x] WebSockets temps reel
- [x] i18n FR/EN/AR + RTL
- [x] Export Excel/PDF (Clients + Appartements + Prospects)
- [x] WhatsApp Meta API (MOCKED - cles requises)
- [x] Resend email (MOCKED - cles requises)
- [x] BIG DATA / PROSPECTS - Module complet avec analytics
- [x] **AUDIT LOG / JOURNAL D'ACTIVITE** - Tracabilite complete:
  - Actions tracees: LOGIN, LOGOUT, CREATE, UPDATE, DELETE, RESTORE, PERMANENT_DELETE
  - Entites: client, prospect, appartement, session
  - Anciennes/nouvelles valeurs enregistrees pour les modifications
  - Interface avec filtres (action, entite, recherche)
  - Donnees immutables (pas de modification/suppression des logs)
- [x] **CORBEILLE / SOFT DELETE** - Suppression reversible:
  - Soft delete sur clients, prospects, appartements (deleted_at, deleted_by)
  - Interface corbeille avec restauration
  - Suppression definitive reservee a l'admin
  - Toutes les operations tracees dans l'audit log
- [x] **API Same-Origin** - Correction cross-origin Safari
- [x] **Seed automatique** au demarrage + endpoint admin /api/admin/seed

## Schema DB
- users: {email, hashed_password, role, name}
- clients: {nom, telephone, telephone2, email, salaire, budget_min, budget_max, objectif, mode_paiement, etage_souhaite, situation_familiale, notes, statut, appartement_id, deleted_at, deleted_by, deleted_by_name}
- residences: {nom, adresse, description}
- appartements: {residence_id, numero_lot, bloc, type_appart, prix, etage, statut, surface, surface_habitable, surface_utile, description, destination, client_id, deleted_at, deleted_by, deleted_by_name}
- prospects: {nom, telephone, telephone2, email, ville, quartier, type_logement, etage_souhaite, nombre_pieces, budget_min, budget_max, mode_paiement, objectif, situation_familiale, notes, source, created_at, created_by, deleted_at, deleted_by, deleted_by_name}
- reservations: {client_id, client_nom, appartement_id, bloc, numero_lot, type_appart, action, agent, date}
- audit_logs: {user_id, user_name, action, entity_type, entity_id, entity_name, old_values, new_values, timestamp} (IMMUTABLE)

## API Endpoints
### Audit & Trash
- GET /api/audit-logs?action=&entity_type=&search=
- GET /api/trash
- POST /api/trash/{entity_type}/{entity_id}/restore
- DELETE /api/trash/{entity_type}/{entity_id}/permanent (admin only)

## Backlog
- P1: Test WhatsApp Meta end-to-end (cles Meta requises)
- P1: Test Resend email (cle API requise)
- P2: Refactoring server.py (1700+ lignes -> decoupe en modules)
