"""
EDIMCO - Complete seed with REAL lot numbers from building PDFs (A-H)
Updates the database with the correct commercial lot numbering.
"""
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

PRIX_M2 = 90000

ALL_LOTS = [
    # === PARKING (Sous-sol) ===
    {"lot": "01", "bloc": "COMMUN", "etage": "Sous-sol", "dest": "Parking", "type": "Parking", "sh": 5070.0, "su": 5070.0},
    # === BLOC A (Lots 224-254) ===
    {"lot": "224", "bloc": "A", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 111.20, "su": 111.20},
    {"lot": "225", "bloc": "A", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 115.20, "su": 115.20},
    {"lot": "226", "bloc": "A", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 16.60, "su": 16.60},
    {"lot": "227", "bloc": "A", "etage": "Etage 02", "dest": "Logement", "type": "F4", "sh": 98.05, "su": 130.85},
    {"lot": "228", "bloc": "A", "etage": "Etage 02", "dest": "Logement", "type": "F2", "sh": 53.20, "su": 81.10},
    {"lot": "229", "bloc": "A", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 82.05, "su": 115.15},
    {"lot": "230", "bloc": "A", "etage": "Etage 03", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "231", "bloc": "A", "etage": "Etage 03", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "232", "bloc": "A", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "233", "bloc": "A", "etage": "Etage 04", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "234", "bloc": "A", "etage": "Etage 04", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "235", "bloc": "A", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "236", "bloc": "A", "etage": "Etage 05", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "237", "bloc": "A", "etage": "Etage 05", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "238", "bloc": "A", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "239", "bloc": "A", "etage": "Etage 06", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "240", "bloc": "A", "etage": "Etage 06", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "241", "bloc": "A", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "242", "bloc": "A", "etage": "Etage 07", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "243", "bloc": "A", "etage": "Etage 07", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "244", "bloc": "A", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "245", "bloc": "A", "etage": "Etage 08", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "246", "bloc": "A", "etage": "Etage 08", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "247", "bloc": "A", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "248", "bloc": "A", "etage": "Etage 09", "dest": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "249", "bloc": "A", "etage": "Etage 09", "dest": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "250", "bloc": "A", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "251", "bloc": "A", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "252", "bloc": "A", "etage": "Etage 10", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "253", "bloc": "A", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "254", "bloc": "A", "etage": "Etage 11", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # === BLOC B (Lots 255-284) ===
    {"lot": "255", "bloc": "B", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 85.60, "su": 85.60},
    {"lot": "256", "bloc": "B", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 111.20, "su": 111.20},
    {"lot": "257", "bloc": "B", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 16.60, "su": 16.60},
    {"lot": "258", "bloc": "B", "etage": "Etage 02", "dest": "Logement", "type": "F4", "sh": 98.05, "su": 130.85},
    {"lot": "259", "bloc": "B", "etage": "Etage 02", "dest": "Logement", "type": "F2", "sh": 53.20, "su": 81.10},
    {"lot": "260", "bloc": "B", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 82.05, "su": 115.15},
    {"lot": "261", "bloc": "B", "etage": "Etage 03", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "262", "bloc": "B", "etage": "Etage 03", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "263", "bloc": "B", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "264", "bloc": "B", "etage": "Etage 04", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "265", "bloc": "B", "etage": "Etage 04", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "266", "bloc": "B", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "267", "bloc": "B", "etage": "Etage 05", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "268", "bloc": "B", "etage": "Etage 05", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "269", "bloc": "B", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "270", "bloc": "B", "etage": "Etage 06", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "271", "bloc": "B", "etage": "Etage 06", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "272", "bloc": "B", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "273", "bloc": "B", "etage": "Etage 07", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "274", "bloc": "B", "etage": "Etage 07", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "275", "bloc": "B", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "276", "bloc": "B", "etage": "Etage 08", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "277", "bloc": "B", "etage": "Etage 08", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "278", "bloc": "B", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "279", "bloc": "B", "etage": "Etage 09", "dest": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "280", "bloc": "B", "etage": "Etage 09", "dest": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "281", "bloc": "B", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "282", "bloc": "B", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "283", "bloc": "B", "etage": "Etage 10", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "284", "bloc": "B", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "285", "bloc": "B", "etage": "Etage 11", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # === BLOC C (Lots 286-334) ===
    {"lot": "286", "bloc": "C", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 108.95, "su": 108.95},
    {"lot": "287", "bloc": "C", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 60.25, "su": 60.25},
    {"lot": "288", "bloc": "C", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 54.60, "su": 54.60},
    {"lot": "289", "bloc": "C", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 108.75, "su": 108.75},
    {"lot": "290", "bloc": "C", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "291", "bloc": "C", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 77.90, "su": 96.10},
    {"lot": "292", "bloc": "C", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "293", "bloc": "C", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "294", "bloc": "C", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "295", "bloc": "C", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "296", "bloc": "C", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 77.90, "su": 96.10},
    {"lot": "297", "bloc": "C", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "298", "bloc": "C", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "299", "bloc": "C", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "300", "bloc": "C", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 94.25},
    {"lot": "301", "bloc": "C", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 77.90, "su": 84.35},
    {"lot": "302", "bloc": "C", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 94.25},
    {"lot": "303", "bloc": "C", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "304", "bloc": "C", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "305", "bloc": "C", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "306", "bloc": "C", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "307", "bloc": "C", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "308", "bloc": "C", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "309", "bloc": "C", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "310", "bloc": "C", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "311", "bloc": "C", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "312", "bloc": "C", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "313", "bloc": "C", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "314", "bloc": "C", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "315", "bloc": "C", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "316", "bloc": "C", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 74.65, "su": 81.10},
    {"lot": "317", "bloc": "C", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "318", "bloc": "C", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 77.35, "su": 84.95},
    {"lot": "319", "bloc": "C", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.60},
    {"lot": "320", "bloc": "C", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "321", "bloc": "C", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 74.65, "su": 81.10},
    {"lot": "322", "bloc": "C", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "323", "bloc": "C", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 77.35, "su": 84.75},
    {"lot": "324", "bloc": "C", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.40},
    {"lot": "325", "bloc": "C", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "326", "bloc": "C", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 74.75, "su": 81.20},
    {"lot": "327", "bloc": "C", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "328", "bloc": "C", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "329", "bloc": "C", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.40},
    {"lot": "330", "bloc": "C", "etage": "Etage 10-11", "dest": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.85},
    {"lot": "331", "bloc": "C", "etage": "Etage 10", "dest": "Logement", "type": "F3", "sh": 74.70, "su": 81.15},
    {"lot": "332", "bloc": "C", "etage": "Etage 10-11", "dest": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.55},
    {"lot": "333", "bloc": "C", "etage": "Etage 10", "dest": "Logement", "type": "F3", "sh": 77.40, "su": 85.00},
    {"lot": "334", "bloc": "C", "etage": "Etage 10", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.60},
    # Bloc C Etage 11 (from EDD data)
    {"lot": "335", "bloc": "C", "etage": "Etage 11", "dest": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "336", "bloc": "C", "etage": "Etage 11", "dest": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "337", "bloc": "C", "etage": "Etage 11", "dest": "Logement", "type": "F3", "sh": 74.10, "su": 81.50},
    # === BLOC D (Lots 338-368) ===
    {"lot": "338", "bloc": "D", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 111.20, "su": 111.20},
    {"lot": "339", "bloc": "D", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 115.20, "su": 115.20},
    {"lot": "340", "bloc": "D", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 16.60, "su": 16.60},
    {"lot": "341", "bloc": "D", "etage": "Etage 02", "dest": "Logement", "type": "F4", "sh": 98.05, "su": 130.85},
    {"lot": "342", "bloc": "D", "etage": "Etage 02", "dest": "Logement", "type": "F2", "sh": 53.20, "su": 81.10},
    {"lot": "343", "bloc": "D", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 82.05, "su": 115.15},
    {"lot": "344", "bloc": "D", "etage": "Etage 03", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "345", "bloc": "D", "etage": "Etage 03", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "346", "bloc": "D", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "347", "bloc": "D", "etage": "Etage 04", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "348", "bloc": "D", "etage": "Etage 04", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "349", "bloc": "D", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "350", "bloc": "D", "etage": "Etage 05", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "351", "bloc": "D", "etage": "Etage 05", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "352", "bloc": "D", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "353", "bloc": "D", "etage": "Etage 06", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "354", "bloc": "D", "etage": "Etage 06", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "355", "bloc": "D", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "356", "bloc": "D", "etage": "Etage 07", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "357", "bloc": "D", "etage": "Etage 07", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "358", "bloc": "D", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "359", "bloc": "D", "etage": "Etage 08", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "360", "bloc": "D", "etage": "Etage 08", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "361", "bloc": "D", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "362", "bloc": "D", "etage": "Etage 09", "dest": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "363", "bloc": "D", "etage": "Etage 09", "dest": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "364", "bloc": "D", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "365", "bloc": "D", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "366", "bloc": "D", "etage": "Etage 10", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "367", "bloc": "D", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "368", "bloc": "D", "etage": "Etage 11", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # === BLOC E (Lots 369-401) ===
    {"lot": "369", "bloc": "E", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 90.55, "su": 90.55},
    {"lot": "370", "bloc": "E", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 56.70, "su": 56.70},
    {"lot": "371", "bloc": "E", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 192.60, "su": 192.60},
    {"lot": "372", "bloc": "E", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 120.00, "su": 120.00},
    {"lot": "373", "bloc": "E", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 16.60, "su": 16.60},
    {"lot": "374", "bloc": "E", "etage": "Etage 02", "dest": "Logement", "type": "F4", "sh": 98.05, "su": 130.90},
    {"lot": "375", "bloc": "E", "etage": "Etage 02", "dest": "Logement", "type": "F2", "sh": 53.20, "su": 83.50},
    {"lot": "376", "bloc": "E", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 82.05, "su": 118.90},
    {"lot": "377", "bloc": "E", "etage": "Etage 03", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "378", "bloc": "E", "etage": "Etage 03", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "379", "bloc": "E", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "380", "bloc": "E", "etage": "Etage 04", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "381", "bloc": "E", "etage": "Etage 04", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "382", "bloc": "E", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "383", "bloc": "E", "etage": "Etage 05", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "384", "bloc": "E", "etage": "Etage 05", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "385", "bloc": "E", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "386", "bloc": "E", "etage": "Etage 06", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "387", "bloc": "E", "etage": "Etage 06", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "388", "bloc": "E", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "389", "bloc": "E", "etage": "Etage 07", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "390", "bloc": "E", "etage": "Etage 07", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "391", "bloc": "E", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "392", "bloc": "E", "etage": "Etage 08", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "393", "bloc": "E", "etage": "Etage 08", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "394", "bloc": "E", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "395", "bloc": "E", "etage": "Etage 09", "dest": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "396", "bloc": "E", "etage": "Etage 09", "dest": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "397", "bloc": "E", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "398", "bloc": "E", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "399", "bloc": "E", "etage": "Etage 10", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "400", "bloc": "E", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "401", "bloc": "E", "etage": "Etage 11", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # === BLOC F (Lots 402-450) ===
    {"lot": "402", "bloc": "F", "etage": "RDC", "dest": "Creche", "type": "Creche", "sh": 320.55, "su": 320.55},
    {"lot": "403", "bloc": "F", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 111.50},
    {"lot": "404", "bloc": "F", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 78.15, "su": 106.35},
    {"lot": "405", "bloc": "F", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 107.80},
    {"lot": "406", "bloc": "F", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 77.10, "su": 84.70},
    {"lot": "407", "bloc": "F", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 73.80, "su": 81.40},
    {"lot": "408", "bloc": "F", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "409", "bloc": "F", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 77.90, "su": 96.10},
    {"lot": "410", "bloc": "F", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 98.30},
    {"lot": "411", "bloc": "F", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "412", "bloc": "F", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "413", "bloc": "F", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 94.25},
    {"lot": "414", "bloc": "F", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 77.90, "su": 84.35},
    {"lot": "415", "bloc": "F", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 80.70, "su": 94.25},
    {"lot": "416", "bloc": "F", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 77.15, "su": 84.55},
    {"lot": "417", "bloc": "F", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 73.85, "su": 81.25},
    {"lot": "418", "bloc": "F", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "419", "bloc": "F", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "420", "bloc": "F", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "421", "bloc": "F", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 77.30, "su": 84.70},
    {"lot": "422", "bloc": "F", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "423", "bloc": "F", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "424", "bloc": "F", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 74.50, "su": 80.95},
    {"lot": "425", "bloc": "F", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.30},
    {"lot": "426", "bloc": "F", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 77.35, "su": 84.70},
    {"lot": "427", "bloc": "F", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 73.95, "su": 81.35},
    {"lot": "428", "bloc": "F", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "429", "bloc": "F", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 74.65, "su": 81.10},
    {"lot": "430", "bloc": "F", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "431", "bloc": "F", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 77.35, "su": 84.95},
    {"lot": "432", "bloc": "F", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.60},
    {"lot": "433", "bloc": "F", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "434", "bloc": "F", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 74.65, "su": 81.10},
    {"lot": "435", "bloc": "F", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 80.90, "su": 94.25},
    {"lot": "436", "bloc": "F", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 77.35, "su": 84.75},
    {"lot": "437", "bloc": "F", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.40},
    {"lot": "438", "bloc": "F", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "439", "bloc": "F", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 74.75, "su": 81.20},
    {"lot": "440", "bloc": "F", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 80.95, "su": 94.35},
    {"lot": "441", "bloc": "F", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "442", "bloc": "F", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 74.05, "su": 81.45},
    {"lot": "443", "bloc": "F", "etage": "Etage 10-11", "dest": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.85},
    {"lot": "444", "bloc": "F", "etage": "Etage 10", "dest": "Logement", "type": "F3", "sh": 74.70, "su": 81.15},
    {"lot": "445", "bloc": "F", "etage": "Etage 10-11", "dest": "Logement", "type": "F5 Duplex", "sh": 142.25, "su": 181.55},
    {"lot": "446", "bloc": "F", "etage": "Etage 10", "dest": "Logement", "type": "F3", "sh": 77.40, "su": 85.00},
    {"lot": "447", "bloc": "F", "etage": "Etage 10", "dest": "Logement", "type": "F3", "sh": 74.00, "su": 81.60},
    {"lot": "448", "bloc": "F", "etage": "Etage 11", "dest": "Logement", "type": "F3", "sh": 74.85, "su": 81.30},
    {"lot": "449", "bloc": "F", "etage": "Etage 11", "dest": "Logement", "type": "F3", "sh": 77.45, "su": 84.85},
    {"lot": "450", "bloc": "F", "etage": "Etage 11", "dest": "Logement", "type": "F3", "sh": 74.10, "su": 81.50},
    # === BLOC G (Lots 451-485) ===
    {"lot": "451", "bloc": "G", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 49.10, "su": 49.10},
    {"lot": "452", "bloc": "G", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 48.95, "su": 48.95},
    {"lot": "453", "bloc": "G", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 76.40, "su": 76.40},
    {"lot": "454", "bloc": "G", "etage": "RDC", "dest": "Service", "type": "Service", "sh": 24.60, "su": 24.60},
    {"lot": "455", "bloc": "G", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 119.15, "su": 119.15},
    {"lot": "456", "bloc": "G", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 172.45, "su": 172.45},
    {"lot": "457", "bloc": "G", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 16.60, "su": 16.60},
    {"lot": "458", "bloc": "G", "etage": "Etage 02", "dest": "Logement", "type": "F4", "sh": 98.05, "su": 124.60},
    {"lot": "459", "bloc": "G", "etage": "Etage 02", "dest": "Logement", "type": "F2", "sh": 53.20, "su": 71.45},
    {"lot": "460", "bloc": "G", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 82.05, "su": 106.60},
    {"lot": "461", "bloc": "G", "etage": "Etage 03", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "462", "bloc": "G", "etage": "Etage 03", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 69.20},
    {"lot": "463", "bloc": "G", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 100.65},
    {"lot": "464", "bloc": "G", "etage": "Etage 04", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "465", "bloc": "G", "etage": "Etage 04", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "466", "bloc": "G", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "467", "bloc": "G", "etage": "Etage 05", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "468", "bloc": "G", "etage": "Etage 05", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "469", "bloc": "G", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "470", "bloc": "G", "etage": "Etage 06", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "471", "bloc": "G", "etage": "Etage 06", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "472", "bloc": "G", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "473", "bloc": "G", "etage": "Etage 07", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "474", "bloc": "G", "etage": "Etage 07", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "475", "bloc": "G", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "476", "bloc": "G", "etage": "Etage 08", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "477", "bloc": "G", "etage": "Etage 08", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "478", "bloc": "G", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "479", "bloc": "G", "etage": "Etage 09", "dest": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "480", "bloc": "G", "etage": "Etage 09", "dest": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "481", "bloc": "G", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "482", "bloc": "G", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "483", "bloc": "G", "etage": "Etage 10", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "484", "bloc": "G", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "485", "bloc": "G", "etage": "Etage 11", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
    # === BLOC H (Lots 486-518) ===
    {"lot": "486", "bloc": "H", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 50.45, "su": 50.45},
    {"lot": "487", "bloc": "H", "etage": "RDC", "dest": "Commerce", "type": "Commerce", "sh": 108.55, "su": 108.55},
    {"lot": "488", "bloc": "H", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 110.65, "su": 110.65},
    {"lot": "489", "bloc": "H", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 180.35, "su": 180.35},
    {"lot": "490", "bloc": "H", "etage": "Etage 01", "dest": "Service", "type": "Service", "sh": 16.60, "su": 16.60},
    {"lot": "491", "bloc": "H", "etage": "Etage 02", "dest": "Logement", "type": "F4", "sh": 98.05, "su": 121.75},
    {"lot": "492", "bloc": "H", "etage": "Etage 02", "dest": "Logement", "type": "F2", "sh": 53.20, "su": 72.30},
    {"lot": "493", "bloc": "H", "etage": "Etage 02", "dest": "Logement", "type": "F3", "sh": 82.05, "su": 112.45},
    {"lot": "494", "bloc": "H", "etage": "Etage 03", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 116.25},
    {"lot": "495", "bloc": "H", "etage": "Etage 03", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "496", "bloc": "H", "etage": "Etage 03", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "497", "bloc": "H", "etage": "Etage 04", "dest": "Logement", "type": "F4", "sh": 98.10, "su": 111.95},
    {"lot": "498", "bloc": "H", "etage": "Etage 04", "dest": "Logement", "type": "F2", "sh": 53.25, "su": 57.35},
    {"lot": "499", "bloc": "H", "etage": "Etage 04", "dest": "Logement", "type": "F3", "sh": 82.10, "su": 96.65},
    {"lot": "500", "bloc": "H", "etage": "Etage 05", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 111.80},
    {"lot": "501", "bloc": "H", "etage": "Etage 05", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "502", "bloc": "H", "etage": "Etage 05", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.65},
    {"lot": "503", "bloc": "H", "etage": "Etage 06", "dest": "Logement", "type": "F4", "sh": 98.25, "su": 112.25},
    {"lot": "504", "bloc": "H", "etage": "Etage 06", "dest": "Logement", "type": "F2", "sh": 53.30, "su": 57.40},
    {"lot": "505", "bloc": "H", "etage": "Etage 06", "dest": "Logement", "type": "F3", "sh": 82.30, "su": 96.35},
    {"lot": "506", "bloc": "H", "etage": "Etage 07", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.55},
    {"lot": "507", "bloc": "H", "etage": "Etage 07", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "508", "bloc": "H", "etage": "Etage 07", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.75},
    {"lot": "509", "bloc": "H", "etage": "Etage 08", "dest": "Logement", "type": "F4", "sh": 98.40, "su": 112.40},
    {"lot": "510", "bloc": "H", "etage": "Etage 08", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "511", "bloc": "H", "etage": "Etage 08", "dest": "Logement", "type": "F3", "sh": 82.40, "su": 96.45},
    {"lot": "512", "bloc": "H", "etage": "Etage 09", "dest": "Logement", "type": "F4", "sh": 98.55, "su": 112.10},
    {"lot": "513", "bloc": "H", "etage": "Etage 09", "dest": "Logement", "type": "F2", "sh": 53.40, "su": 57.50},
    {"lot": "514", "bloc": "H", "etage": "Etage 09", "dest": "Logement", "type": "F3", "sh": 82.55, "su": 96.55},
    {"lot": "515", "bloc": "H", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 146.90, "su": 221.10},
    {"lot": "516", "bloc": "H", "etage": "Etage 10", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.45},
    {"lot": "517", "bloc": "H", "etage": "Etage 10-11", "dest": "Logement", "type": "F4 Duplex", "sh": 134.20, "su": 189.80},
    {"lot": "518", "bloc": "H", "etage": "Etage 11", "dest": "Logement", "type": "F2", "sh": 53.35, "su": 57.40},
]


async def seed():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]

    residence = await db.residences.find_one({"nom": "EDIMCO"})
    if not residence:
        result = await db.residences.insert_one({
            "nom": "EDIMCO",
            "adresse": "EDIMCO, Commune de Bejaia, Wilaya de Bejaia",
            "description": "Residence DJERBA - 264 logements promotionnels R+11",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        residence_id = str(result.inserted_id)
    else:
        residence_id = str(residence["_id"])

    deleted = await db.appartements.delete_many({})
    print(f"Cleared {deleted.deleted_count} old apartments")

    docs = []
    for lot in ALL_LOTS:
        if lot["dest"] == "Logement":
            prix = round(lot["sh"] * PRIX_M2, 2)
        else:
            prix = 0

        docs.append({
            "residence_id": residence_id,
            "numero_lot": lot["lot"],
            "bloc": lot["bloc"],
            "type_appart": lot["type"],
            "prix": prix,
            "etage": lot["etage"],
            "statut": "disponible",
            "surface": lot["sh"],
            "surface_habitable": lot["sh"],
            "surface_utile": lot["su"],
            "description": "",
            "destination": lot["dest"],
            "client_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    result = await db.appartements.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} lots")

    # Summary
    by_dest = {}
    by_bloc = {}
    by_type = {}
    for d in docs:
        by_dest[d["destination"]] = by_dest.get(d["destination"], 0) + 1
        if d["destination"] == "Logement":
            by_bloc[d["bloc"]] = by_bloc.get(d["bloc"], 0) + 1
            by_type[d["type_appart"]] = by_type.get(d["type_appart"], 0) + 1

    print(f"\n=== RESUME ===")
    print(f"Total: {len(docs)}")
    for k, v in sorted(by_dest.items()):
        print(f"  {k}: {v}")
    print(f"\nPar bloc (logements):")
    for k, v in sorted(by_bloc.items()):
        print(f"  Bloc {k}: {v}")
    print(f"\nPar type:")
    for k, v in sorted(by_type.items()):
        print(f"  {k}: {v}")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed())
