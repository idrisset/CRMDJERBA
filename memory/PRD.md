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
- [x] Systeme de reservation + historique
- [x] Detection de conflit (409 si appart deja reserve)
- [x] Dashboard interactif cliquable (stats, blocs, statuts)
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
- [x] Page Administration - Gestion utilisateurs + approbations
- [x] Page Clients en Double - Detection et fusion
- [x] SAUVEGARDE & RESTAURATION complète :
  - Automatique 6h + quotidien 02h00
  - Manuelle via bouton
  - Restauration avec backup sécurité auto
  - Journal des sauvegardes
  - Rétention 7j + 4sem + 3mois
  - Email alerte (Resend)
  - Export ZIP téléchargeable

## Backlog
- P1: Test WhatsApp Meta end-to-end (cles Meta requises)
- P2: Refactoring server.py en modules séparés
