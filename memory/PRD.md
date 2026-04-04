# DJERBA CONSTRUCTION - CRM EDIMCO

## Probleme Original
CRM interne pour DJERBA CONSTRUCTION (Algerie) - gestion clients et appartements du projet EDIMCO (Residence DJERBA).

## Architecture
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Auth: JWT localStorage (iPad/Safari compatible)
- Design: Luxury (Navy #1E3A5F / Red #C41E3A / White)
- i18n: FR, EN, AR (RTL)
- Temps reel: WebSockets

## Donnees EDIMCO (Lots 224-518)
Total: 296 lots | 264 logements | 8 commerces | 22 services | 1 parking | 1 creche

| Bloc | Lots | Logements | Types |
|------|------|-----------|-------|
| A | 224-254 | 28 | F2, F3, F4, F4 Duplex |
| B | 255-285 | 28 | F2, F3, F4, F4 Duplex |
| C | 286-337 | 48 | F3, F5 Duplex |
| D | 338-368 | 28 | F2, F3, F4, F4 Duplex |
| E | 369-401 | 28 | F2, F3, F4, F4 Duplex |
| F | 402-450 | 48 | F3, F5 Duplex |
| G | 451-485 | 28 | F2, F3, F4, F4 Duplex |
| H | 486-518 | 28 | F2, F3, F4, F4 Duplex |

Prix: 90 000 DA/m2 TTC (surface habitable)

## Fonctionnalites
- [x] Auth JWT localStorage
- [x] Gestion clients (CRUD, statuts, temperature)
- [x] Gestion residences
- [x] Gestion appartements avec onglets par type (F2/F3/F4/Duplex/Commerce/Service)
- [x] Filtres par bloc + recherche par lot
- [x] Tableau de bord avec stats par bloc
- [x] WebSockets temps reel
- [x] i18n FR/EN/AR + RTL
- [x] Export Excel
- [x] WhatsApp Meta API (code en place)
- [x] Resend email (code en place)

## Backlog
- P1: Test WhatsApp Meta end-to-end (cles Meta requises)
- P2: Test exports PDF/Excel
- P3: Refactoring server.py

## Schema DB
- users: {email, hashed_password, role, name}
- clients: {nom, telephone, email, salaire, situation_familiale, notes, statut, temperature, source}
- residences: {nom, adresse, description}
- appartements: {residence_id, numero_lot, bloc, type_appart, prix, etage, statut, surface, surface_habitable, surface_utile, description, destination, client_id}
