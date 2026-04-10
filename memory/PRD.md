# DJERBA CONSTRUCTION - CRM EDIMCO

## Probleme Original
CRM interne pour DJERBA CONSTRUCTION (Algerie) - gestion clients et appartements du projet EDIMCO.
Système multi-utilisateurs avec 3 rôles (Super Admin, Admin Limité, Utilisateur).

## Architecture
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Auth: JWT localStorage (iPad/Safari compatible)
- Design: Luxury (Navy #1E3A5F / Red #C41E3A / White)
- i18n: FR, EN, AR (RTL)
- Real-time: WebSockets
- API: Same-origin relative URLs (no cross-origin)
- Email: Resend API (clé configurée)

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
- [x] Resend email (cle API configurée)
- [x] BIG DATA / PROSPECTS - Module complet avec analytics
- [x] AUDIT LOG / JOURNAL D'ACTIVITE - Tracabilite complete
- [x] CORBEILLE / SOFT DELETE - Suppression reversible
- [x] API Same-Origin - Correction cross-origin Safari
- [x] Seed automatique au demarrage + endpoint admin /api/admin/seed
- [x] **RBAC Multi-Utilisateurs** - 3 rôles:
  - Super Administrateur (level 3): Accès total, gestion utilisateurs, approbations
  - Administrateur Limité (level 2): CRUD normal, demande approbation pour suppression
  - Utilisateur (level 1): Accès basique, demande approbation pour actions sensibles
- [x] **Système d'Approbation** - Workflow complet:
  - Demande automatique pour actions sensibles (suppression)
  - Notification email via Resend aux super admins
  - Interface approbation dans page Admin (Approuver/Rejeter)
  - Historique des demandes
- [x] **Références Clients Auto** - #001, #002, #003...
- [x] **Détection Doublons** - Par téléphone, nom, email
  - Warning avant création de doublon
  - Option "Créer quand même" (force_create)
  - Page dédiée "Clients en double" avec fusion
- [x] **Multi-Appartements par Client** - Un client peut réserver/acheter plusieurs lots
  - Sélection multiple dans le formulaire client
  - Affichage multi-lots dans le tableau
  - Gestion cohérente lors de la mise à jour/suppression
- [x] **Dashboard Interactif** - Tout est cliquable:
  - Cartes stats → pages filtrées (disponible/réservé/vendu)
  - Blocs A-H → appartements filtrés par bloc
  - Statuts clients → clients filtrés par statut
- [x] **Page Administration** - Gestion utilisateurs + approbations
  - Création/modification utilisateurs avec rôles
  - Désactivation de comptes
  - Onglets: Utilisateurs, Approbations en attente, Historique
- [x] **Page Clients en Double** - Détection et fusion de doublons
  - Groupes de doublons par téléphone/nom/email
  - Interface de fusion (garder un, fusionner l'autre)

## Schema DB
- users: {email, password_hash, role (super_admin|admin_limited|user), name, is_active}
- clients: {reference (#001), nom, telephone, telephone2, email, salaire, budget_min, budget_max, objectif, mode_paiement, etage_souhaite, situation_familiale, notes, statut, appartement_ids (Array), deleted_at, deleted_by}
- appartements: {residence_id, numero_lot, bloc, type_appart, prix, etage, statut, surface, surface_habitable, surface_utile, destination, client_id, deleted_at}
- prospects: {nom, telephone, ville, type_logement, deleted_at}
- reservations: {client_id, client_nom, appartement_id, bloc, numero_lot, type_appart, action, agent, date}
- audit_logs: {user_id, user_name, action, entity_type, entity_id, entity_name, old_values, new_values, timestamp}
- approval_requests: {requester_id, requester_name, requester_role, action, entity_type, entity_id, entity_name, details, status (pending|approved|rejected), reviewed_by, reviewed_at}

## API Endpoints
### Auth
- POST /api/auth/login, /api/auth/register, /api/auth/logout, /api/auth/refresh
- GET /api/auth/me (returns permissions)
- PUT /api/auth/change-password

### Users (Super Admin only)
- GET /api/users
- POST /api/users
- PUT /api/users/{id}
- DELETE /api/users/{id} (deactivate)

### Approvals
- GET /api/approvals, /api/approvals/count
- POST /api/approvals/{id}/approve, /api/approvals/{id}/reject

### Clients
- GET /api/clients, POST /api/clients (with duplicate detection)
- PUT /api/clients/{id}, DELETE /api/clients/{id} (RBAC)
- POST /api/clients/check-duplicates
- GET /api/clients/duplicates
- POST /api/clients/merge/{keep_id}/{merge_id}

### Appartements, Prospects, Residences, Audit, Trash
- Full CRUD with RBAC protection

## Backlog
- P1: Test WhatsApp Meta end-to-end (clés Meta requises)
- P2: Refactoring server.py (2400+ lignes -> decoupe en modules)
