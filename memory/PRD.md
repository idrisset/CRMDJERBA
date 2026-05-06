# DJERBA CONSTRUCTION - CRM EDIMCO

## Probleme Original
CRM interne pour DJERBA CONSTRUCTION (Algerie) - gestion clients et appartements du projet EDIMCO.

## Architecture
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Auth: JWT localStorage
- Email: Resend API
- Backup: mongodump/mongorestore + APScheduler

## Fonctionnalites
- [x] Auth JWT + RBAC 3 rôles (super_admin/admin_limited/user)
- [x] Dashboard interactif cliquable
- [x] Gestion clients (CRUD, multi-appartements, references auto, doublons)
- [x] Gestion appartements (onglets par type, blocs A-H)
- [x] Prospects / Big Data
- [x] Systeme d'approbation + email Resend
- [x] Audit Log + Corbeille (soft delete)
- [x] i18n FR/EN/AR + WebSockets temps reel
- [x] Export Excel/PDF
- [x] Administration (gestion utilisateurs, approbations)
- [x] Sauvegarde complète :
  - Auto 6h + quotidien 02h00
  - Manuelle via bouton
  - Restauration avec backup sécurité auto
  - Journal des sauvegardes
  - Rétention 7j + 4sem + 3mois
  - Export ZIP téléchargeable
  - **Export hebdomadaire par email (dimanche 03h00)**
  - Toggle on/off + email configurable + bouton test
- [x] Login page refonte design (mockup fidèle)
- [x] Système d'alertes sécurité login:
  - Email inconnu → alerte admin
  - 5 échecs consécutifs → blocage 15min + alerte admin
  - Connexion nouvelle IP → alerte utilisateur
  - Géolocalisation IP via ipapi.co
  - Collection login_attempts en DB
  - Templates HTML brandés (navy #172D66 + rouge #EF2A45)
- [x] Suppression inscription publique (route /register supprimée)

## Backlog
- P1: Test WhatsApp Meta end-to-end
- P2: Refactoring server.py en modules
