"""
Seed script for EDIMCO / Résidence DJERBA
264 logements + 8 commerces + 25 services + 1 parking
8 bâtiments (A-H), R+11, Duplex 10e-11e étage
Prix: 90 000 DA/m² TTC pour les logements
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

PRIX_M2 = 90000  # DA/m² TTC

ALL_LOTS = [
    {"lot": "01", "bloc": "COMMUN", "etage": "Sous-sol", "destination": "Parking", "type": None, "sh": 5070.0, "su": 5070.0},
    {"lot": "02", "bloc": "F", "etage": "Sous-sol", "destination": "Service", "type": None, "sh": 42.30, "su": 42.30},
    {"lot": "03", "bloc": "A", "etage": "RDC", "destination": "Service", "type": None, "sh": 111.20, "su": 111.20},
    {"lot": "04", "bloc": "A", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 115.20, "su": 115.20},
    {"lot": "05", "bloc": "A", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 16.60, "su": 16.60},
    {"lot": "06", "bloc": "A", "etage": "Etage 02", "destination": "Logement", "type": "F4", "sh": 98.05, "su": 130.85},
    {"lot": "07", "bloc": "A", "etage": "Etage 02", "destination": "Logement", "type": "F2", "sh": 53.20, "su": 81.10},
    {"lot": "08", "bloc": "A", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 82.05, "su": 115.15},
    {"lot": "09", "bloc": "A", "etage": "Etage 03", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "10", "bloc": "A", "etage": "Etage 03", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "11", "bloc": "A", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "12", "bloc": "A", "etage": "Etage 04", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "13", "bloc": "A", "etage": "Etage 04", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "14", "bloc": "A", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "15", "bloc": "A", "etage": "Etage 05", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "16", "bloc": "A", "etage": "Etage 05", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "17", "bloc": "A", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "18", "bloc": "A", "etage": "Etage 06", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "19", "bloc": "A", "etage": "Etage 06", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "20", "bloc": "A", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "21", "bloc": "A", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "22", "bloc": "A", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "23", "bloc": "A", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "24", "bloc": "A", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "25", "bloc": "A", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "26", "bloc": "A", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "27", "bloc": "A", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "28", "bloc": "A", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "29", "bloc": "A", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "30", "bloc": "A", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "31", "bloc": "A", "etage": "Etage 10", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "32", "bloc": "A", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "33", "bloc": "A", "etage": "Etage 11", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # Bloc B
    {"lot": "34", "bloc": "B", "etage": "RDC", "destination": "Service", "type": None, "sh": 111.20, "su": 111.20},
    {"lot": "35", "bloc": "B", "etage": "RDC", "destination": "Service", "type": None, "sh": 85.60, "su": 85.60},
    {"lot": "36", "bloc": "B", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 16.60, "su": 16.60},
    {"lot": "37", "bloc": "B", "etage": "Etage 02", "destination": "Logement", "type": "F4", "sh": 98.05, "su": 130.85},
    {"lot": "38", "bloc": "B", "etage": "Etage 02", "destination": "Logement", "type": "F2", "sh": 53.20, "su": 81.10},
    {"lot": "39", "bloc": "B", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 82.05, "su": 115.15},
    {"lot": "40", "bloc": "B", "etage": "Etage 03", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "41", "bloc": "B", "etage": "Etage 03", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "42", "bloc": "B", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "43", "bloc": "B", "etage": "Etage 04", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "44", "bloc": "B", "etage": "Etage 04", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "45", "bloc": "B", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "46", "bloc": "B", "etage": "Etage 05", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "47", "bloc": "B", "etage": "Etage 05", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "48", "bloc": "B", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "49", "bloc": "B", "etage": "Etage 06", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "50", "bloc": "B", "etage": "Etage 06", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "51", "bloc": "B", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "52", "bloc": "B", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "53", "bloc": "B", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "54", "bloc": "B", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "55", "bloc": "B", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "56", "bloc": "B", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "57", "bloc": "B", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "58", "bloc": "B", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "59", "bloc": "B", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "60", "bloc": "B", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "61", "bloc": "B", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "62", "bloc": "B", "etage": "Etage 10", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "63", "bloc": "B", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "64", "bloc": "B", "etage": "Etage 11", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # Bloc C
    {"lot": "65", "bloc": "C", "etage": "RDC", "destination": "Service", "type": None, "sh": 108.95, "su": 108.95},
    {"lot": "66", "bloc": "C", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 54.60, "su": 54.60},
    {"lot": "67", "bloc": "C", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 60.25, "su": 60.25},
    {"lot": "68", "bloc": "C", "etage": "RDC", "destination": "Service", "type": None, "sh": 108.75, "su": 108.75},
    {"lot": "69", "bloc": "C", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 112.70},
    {"lot": "70", "bloc": "C", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 78.15, "su": 111.60},
    {"lot": "71", "bloc": "C", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 112.70},
    {"lot": "72", "bloc": "C", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 77.10, "su": 84.70},
    {"lot": "73", "bloc": "C", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 73.80, "su": 81.40},
    {"lot": "74", "bloc": "C", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "75", "bloc": "C", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 77.90, "su": 96.10},
    {"lot": "76", "bloc": "C", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "77", "bloc": "C", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "78", "bloc": "C", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "79", "bloc": "C", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 94.25},
    {"lot": "80", "bloc": "C", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 77.90, "su": 84.35},
    {"lot": "81", "bloc": "C", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "82", "bloc": "C", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "83", "bloc": "C", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "84", "bloc": "C", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "85", "bloc": "C", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "86", "bloc": "C", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "87", "bloc": "C", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "88", "bloc": "C", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.35},
    {"lot": "89", "bloc": "C", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "90", "bloc": "C", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "91", "bloc": "C", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "92", "bloc": "C", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.35},
    {"lot": "93", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "94", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "95", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "96", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "97", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "98", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    {"lot": "99", "bloc": "C", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "100", "bloc": "C", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "101", "bloc": "C", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "102", "bloc": "C", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "103", "bloc": "C", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "104", "bloc": "C", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "105", "bloc": "C", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "106", "bloc": "C", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "107", "bloc": "C", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "108", "bloc": "C", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 74.05, "su": 81.45},
    {"lot": "109", "bloc": "C", "etage": "Etage 10-11", "destination": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.85},
    {"lot": "110", "bloc": "C", "etage": "Etage 10", "destination": "Logement", "type": "F3", "sh": 74.70, "su": 81.15},
    {"lot": "111", "bloc": "C", "etage": "Etage 10-11", "destination": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.55},
    {"lot": "112", "bloc": "C", "etage": "Etage 10", "destination": "Logement", "type": "F3", "sh": 77.40, "su": 85.00},
    {"lot": "113", "bloc": "C", "etage": "Etage 10", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.60},
    {"lot": "114", "bloc": "C", "etage": "Etage 11", "destination": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "115", "bloc": "C", "etage": "Etage 11", "destination": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "116", "bloc": "C", "etage": "Etage 11", "destination": "Logement", "type": "F3", "sh": 74.10, "su": 81.50},
    # Bloc D
    {"lot": "117", "bloc": "D", "etage": "RDC", "destination": "Service", "type": None, "sh": 85.60, "su": 85.60},
    {"lot": "118", "bloc": "D", "etage": "RDC", "destination": "Service", "type": None, "sh": 111.20, "su": 111.20},
    {"lot": "119", "bloc": "D", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 16.60, "su": 16.60},
    {"lot": "120", "bloc": "D", "etage": "Etage 02", "destination": "Logement", "type": "F4", "sh": 98.05, "su": 130.85},
    {"lot": "121", "bloc": "D", "etage": "Etage 02", "destination": "Logement", "type": "F2", "sh": 53.20, "su": 81.10},
    {"lot": "122", "bloc": "D", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 82.05, "su": 115.15},
    {"lot": "123", "bloc": "D", "etage": "Etage 03", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "124", "bloc": "D", "etage": "Etage 03", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "125", "bloc": "D", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "126", "bloc": "D", "etage": "Etage 04", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "127", "bloc": "D", "etage": "Etage 04", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "128", "bloc": "D", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "129", "bloc": "D", "etage": "Etage 05", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "130", "bloc": "D", "etage": "Etage 05", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "131", "bloc": "D", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "132", "bloc": "D", "etage": "Etage 06", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "133", "bloc": "D", "etage": "Etage 06", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "134", "bloc": "D", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "135", "bloc": "D", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "136", "bloc": "D", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "137", "bloc": "D", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "138", "bloc": "D", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "139", "bloc": "D", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "140", "bloc": "D", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "141", "bloc": "D", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "142", "bloc": "D", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "143", "bloc": "D", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "144", "bloc": "D", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "145", "bloc": "D", "etage": "Etage 10", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "146", "bloc": "D", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "147", "bloc": "D", "etage": "Etage 11", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # Bloc E
    {"lot": "148", "bloc": "E", "etage": "RDC", "destination": "Service", "type": None, "sh": 22.75, "su": 22.75},
    {"lot": "149", "bloc": "E", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 90.55, "su": 90.55},
    {"lot": "150", "bloc": "E", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 56.70, "su": 56.70},
    {"lot": "151", "bloc": "E", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 192.60, "su": 192.60},
    {"lot": "152", "bloc": "E", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 120.00, "su": 120.00},
    {"lot": "153", "bloc": "E", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 16.60, "su": 16.60},
    {"lot": "154", "bloc": "E", "etage": "Etage 02", "destination": "Logement", "type": "F4", "sh": 98.05, "su": 130.90},
    {"lot": "155", "bloc": "E", "etage": "Etage 02", "destination": "Logement", "type": "F2", "sh": 53.20, "su": 83.50},
    {"lot": "156", "bloc": "E", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 82.05, "su": 118.90},
    {"lot": "157", "bloc": "E", "etage": "Etage 03", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "158", "bloc": "E", "etage": "Etage 03", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "159", "bloc": "E", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "160", "bloc": "E", "etage": "Etage 04", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "161", "bloc": "E", "etage": "Etage 04", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "162", "bloc": "E", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "163", "bloc": "E", "etage": "Etage 05", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "164", "bloc": "E", "etage": "Etage 05", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "165", "bloc": "E", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "166", "bloc": "E", "etage": "Etage 06", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "167", "bloc": "E", "etage": "Etage 06", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "168", "bloc": "E", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "169", "bloc": "E", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "170", "bloc": "E", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "171", "bloc": "E", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "172", "bloc": "E", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "173", "bloc": "E", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "174", "bloc": "E", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "175", "bloc": "E", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "176", "bloc": "E", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "177", "bloc": "E", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "178", "bloc": "E", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "179", "bloc": "E", "etage": "Etage 10", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "180", "bloc": "E", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "181", "bloc": "E", "etage": "Etage 11", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # Bloc F
    {"lot": "182", "bloc": "F", "etage": "RDC", "destination": "Creche", "type": None, "sh": 320.55, "su": 320.55},
    {"lot": "183", "bloc": "F", "etage": "Etage 01", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 111.50},
    {"lot": "184", "bloc": "F", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 78.15, "su": 106.35},
    {"lot": "185", "bloc": "F", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 107.80},
    {"lot": "186", "bloc": "F", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 77.10, "su": 84.70},
    {"lot": "187", "bloc": "F", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 73.80, "su": 81.40},
    {"lot": "188", "bloc": "F", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "189", "bloc": "F", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 77.90, "su": 96.10},
    {"lot": "190", "bloc": "F", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "191", "bloc": "F", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "192", "bloc": "F", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "193", "bloc": "F", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 80.70, "su": 94.25},
    {"lot": "194", "bloc": "F", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 77.90, "su": 84.35},
    {"lot": "195", "bloc": "F", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "196", "bloc": "F", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "197", "bloc": "F", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "198", "bloc": "F", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "199", "bloc": "F", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "200", "bloc": "F", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "201", "bloc": "F", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "202", "bloc": "F", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "203", "bloc": "F", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "204", "bloc": "F", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "205", "bloc": "F", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "206", "bloc": "F", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "207", "bloc": "F", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "208", "bloc": "F", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "209", "bloc": "F", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "210", "bloc": "F", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.40},
    {"lot": "211", "bloc": "F", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "212", "bloc": "F", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "213", "bloc": "F", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "214", "bloc": "F", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.35},
    {"lot": "215", "bloc": "F", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "216", "bloc": "F", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "217", "bloc": "F", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 74.05, "su": 81.45},
    {"lot": "218", "bloc": "F", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "219", "bloc": "F", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 74.75, "su": 81.20},
    {"lot": "220", "bloc": "F", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "221", "bloc": "F", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "222", "bloc": "F", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.35},
    {"lot": "223", "bloc": "F", "etage": "Etage 10-11", "destination": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.85},
    {"lot": "224", "bloc": "F", "etage": "Etage 10", "destination": "Logement", "type": "F3", "sh": 74.70, "su": 81.15},
    {"lot": "225", "bloc": "F", "etage": "Etage 10-11", "destination": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.55},
    {"lot": "226", "bloc": "F", "etage": "Etage 10", "destination": "Logement", "type": "F3", "sh": 77.40, "su": 85.00},
    {"lot": "227", "bloc": "F", "etage": "Etage 10", "destination": "Logement", "type": "F3", "sh": 74.00, "su": 81.60},
    {"lot": "228", "bloc": "F", "etage": "Etage 11", "destination": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "229", "bloc": "F", "etage": "Etage 11", "destination": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "230", "bloc": "F", "etage": "Etage 11", "destination": "Logement", "type": "F3", "sh": 74.10, "su": 81.50},
    # Bloc G
    {"lot": "231", "bloc": "G", "etage": "RDC", "destination": "Service", "type": None, "sh": 49.10, "su": 49.10},
    {"lot": "232", "bloc": "G", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 48.95, "su": 48.95},
    {"lot": "233", "bloc": "G", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 76.40, "su": 76.40},
    {"lot": "234", "bloc": "G", "etage": "RDC", "destination": "Service", "type": None, "sh": 24.60, "su": 24.60},
    {"lot": "235", "bloc": "G", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 119.15, "su": 119.15},
    {"lot": "236", "bloc": "G", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 172.45, "su": 172.45},
    {"lot": "237", "bloc": "G", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 16.60, "su": 16.60},
    {"lot": "238", "bloc": "G", "etage": "Etage 02", "destination": "Logement", "type": "F4", "sh": 98.05, "su": 124.60},
    {"lot": "239", "bloc": "G", "etage": "Etage 02", "destination": "Logement", "type": "F2", "sh": 53.20, "su": 71.45},
    {"lot": "240", "bloc": "G", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 82.05, "su": 106.60},
    {"lot": "241", "bloc": "G", "etage": "Etage 03", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "242", "bloc": "G", "etage": "Etage 03", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "243", "bloc": "G", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "244", "bloc": "G", "etage": "Etage 04", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "245", "bloc": "G", "etage": "Etage 04", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "246", "bloc": "G", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "247", "bloc": "G", "etage": "Etage 05", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "248", "bloc": "G", "etage": "Etage 05", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "249", "bloc": "G", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "250", "bloc": "G", "etage": "Etage 06", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "251", "bloc": "G", "etage": "Etage 06", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "252", "bloc": "G", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "253", "bloc": "G", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "254", "bloc": "G", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "255", "bloc": "G", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "256", "bloc": "G", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "257", "bloc": "G", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "258", "bloc": "G", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "259", "bloc": "G", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "260", "bloc": "G", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "261", "bloc": "G", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "262", "bloc": "G", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "263", "bloc": "G", "etage": "Etage 10", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "264", "bloc": "G", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "265", "bloc": "G", "etage": "Etage 11", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # Bloc H
    {"lot": "266", "bloc": "H", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 50.45, "su": 50.45},
    {"lot": "267", "bloc": "H", "etage": "RDC", "destination": "Commerce", "type": None, "sh": 108.55, "su": 108.55},
    {"lot": "268", "bloc": "H", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 110.65, "su": 110.65},
    {"lot": "269", "bloc": "H", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 180.35, "su": 180.35},
    {"lot": "270", "bloc": "H", "etage": "Etage 01", "destination": "Service", "type": None, "sh": 16.60, "su": 16.60},
    {"lot": "271", "bloc": "H", "etage": "Etage 02", "destination": "Logement", "type": "F4", "sh": 98.05, "su": 121.75},
    {"lot": "272", "bloc": "H", "etage": "Etage 02", "destination": "Logement", "type": "F2", "sh": 53.20, "su": 72.30},
    {"lot": "273", "bloc": "H", "etage": "Etage 02", "destination": "Logement", "type": "F3", "sh": 82.05, "su": 112.45},
    {"lot": "274", "bloc": "H", "etage": "Etage 03", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "275", "bloc": "H", "etage": "Etage 03", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "276", "bloc": "H", "etage": "Etage 03", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "277", "bloc": "H", "etage": "Etage 04", "destination": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "278", "bloc": "H", "etage": "Etage 04", "destination": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "279", "bloc": "H", "etage": "Etage 04", "destination": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "280", "bloc": "H", "etage": "Etage 05", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "281", "bloc": "H", "etage": "Etage 05", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "282", "bloc": "H", "etage": "Etage 05", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "283", "bloc": "H", "etage": "Etage 06", "destination": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "284", "bloc": "H", "etage": "Etage 06", "destination": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "285", "bloc": "H", "etage": "Etage 06", "destination": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "286", "bloc": "H", "etage": "Etage 07", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "287", "bloc": "H", "etage": "Etage 07", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "288", "bloc": "H", "etage": "Etage 07", "destination": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "289", "bloc": "H", "etage": "Etage 08", "destination": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "290", "bloc": "H", "etage": "Etage 08", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "291", "bloc": "H", "etage": "Etage 08", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "292", "bloc": "H", "etage": "Etage 09", "destination": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "293", "bloc": "H", "etage": "Etage 09", "destination": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "294", "bloc": "H", "etage": "Etage 09", "destination": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "295", "bloc": "H", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "296", "bloc": "H", "etage": "Etage 10", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "297", "bloc": "H", "etage": "Etage 10-11", "destination": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "298", "bloc": "H", "etage": "Etage 11", "destination": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
]


async def seed():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]

    # Get EDIMCO residence ID
    residence = await db.residences.find_one({"nom": "EDIMCO"})
    if not residence:
        result = await db.residences.insert_one({
            "nom": "EDIMCO",
            "adresse": "EDIMCO, Commune de Bejaia, Wilaya de Bejaia",
            "description": "Residence DJERBA - 264 logements promotionnels R+11",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        residence_id = str(result.inserted_id)
        print(f"Created EDIMCO residence: {residence_id}")
    else:
        residence_id = str(residence["_id"])
        print(f"Using existing EDIMCO residence: {residence_id}")

    # Clear existing apartments
    deleted = await db.appartements.delete_many({})
    print(f"Cleared {deleted.deleted_count} existing apartments")

    # Insert all lots
    docs = []
    for lot in ALL_LOTS:
        # Calculate price for apartments (90,000 DA/m2 for habitable surface)
        if lot["destination"] == "Logement" and lot["type"]:
            prix = round(lot["sh"] * PRIX_M2, 2)
        elif lot["destination"] == "Parking":
            prix = 0  # Parking is rented
        else:
            prix = 0  # Commerce/Service prices TBD

        doc = {
            "residence_id": residence_id,
            "numero_lot": lot["lot"],
            "bloc": lot["bloc"],
            "type_appart": lot["type"] or lot["destination"],
            "prix": prix,
            "etage": lot["etage"],
            "statut": "disponible",
            "surface": lot["sh"],
            "surface_habitable": lot["sh"],
            "surface_utile": lot["su"],
            "description": "",
            "destination": lot["destination"],
            "client_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        docs.append(doc)

    result = await db.appartements.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} lots")

    # Summary
    logements = [d for d in docs if d["destination"] == "Logement"]
    commerces = [d for d in docs if d["destination"] == "Commerce"]
    services = [d for d in docs if d["destination"] == "Service"]
    parking = [d for d in docs if d["destination"] == "Parking"]
    creche = [d for d in docs if d["destination"] == "Creche"]

    print(f"\n=== RESUME ===")
    print(f"Total lots: {len(docs)}")
    print(f"Logements: {len(logements)}")
    print(f"Commerces: {len(commerces)}")
    print(f"Services: {len(services)}")
    print(f"Parking: {len(parking)}")
    print(f"Creche: {len(creche)}")

    # Type breakdown
    types = {}
    for d in logements:
        t = d["type_appart"]
        types[t] = types.get(t, 0) + 1
    print(f"\nPar type:")
    for t, count in sorted(types.items()):
        print(f"  {t}: {count}")

    # Bloc breakdown
    blocs = {}
    for d in logements:
        b = d["bloc"]
        blocs[b] = blocs.get(b, 0) + 1
    print(f"\nPar bloc:")
    for b, count in sorted(blocs.items()):
        print(f"  Bloc {b}: {count} logements")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
