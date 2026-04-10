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
- Email: Resend API
- Backup: mongodump/mongorestore + APScheduler

## Fonctionnalites Implementees
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
- [x] BIG DATA / PROSPECTS - Module complet avec analytics
- [x] AUDIT LOG / JOURNAL D'ACTIVITE - Tracabilite complete
- [x] CORBEILLE / SOFT DELETE - Suppression reversible
- [x] RBAC Multi-Utilisateurs - 3 roles (super_admin/admin_limited/user)
- [x] Systeme d'Approbation - Workflow complet avec email Resend
- [x] References Clients Auto - #001, #002, #003...
- [x] Detection Doublons - Par telephone, nom, email + Page fusion
- [x] Multi-Appartements par Client - Selection multiple
- [x] Dashboard Interactif - Tout cliquable (stats, blocs, statuts)
- [x] Page Administration - Gestion utilisateurs + approbations
- [x] Page Clients en Double - Detection et fusion
- [x] **SAUVEGARDE & RESTAURATION** :
  - Sauvegarde automatique toutes les 6 heures
  - Sauvegarde quotidienne a 02h00
  - Sauvegarde manuelle via bouton
  - Restauration avec sauvegarde de securite automatique
  - Journal des sauvegardes (date, type, statut, taille)
  - Politique de retention: 7 jours + 4 semaines + 3 mois
  - Email d'alerte en cas d'echec ou restauration
  - Protection RBAC (Super Admin uniquement)

## Schema DB
- users: {email, password_hash, role, name, is_active}
- clients: {reference, nom, telephone, telephone2, email, salaire, budget_min, budget_max, objectif, mode_paiement, etage_souhaite, situation_familiale, notes, statut, appartement_ids, deleted_at}
- appartements: {residence_id, numero_lot, bloc, type_appart, prix, etage, statut, surface, client_id, deleted_at}
- prospects: {nom, telephone, ville, type_logement, deleted_at}
- reservations: {client_id, client_nom, appartement_id, bloc, numero_lot, type_appart, action, agent, date}
- audit_logs: {user_id, user_name, action, entity_type, entity_id, entity_name, old_values, new_values, timestamp}
- approval_requests: {requester_id, requester_name, action, entity_type, entity_id, entity_name, details, status}
- backups: {backup_id, type, triggered_by, status, size_mb, created_at, completed_at, error}

## Backlog
- P1: Test WhatsApp Meta end-to-end (cles Meta requises)
- P2: Refactoring server.py (2600+ lignes -> decoupe en modules)
