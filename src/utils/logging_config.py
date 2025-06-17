"""
Zentrale Konfiguration für das Logging-System des energyOS-Projekts.
"""

import logging
import sys
from pathlib import Path

# Definiere globale Log-Level-Konstanten
LOG_LEVEL_CONSOLE = logging.INFO  # Standard-Level für die Konsole
LOG_LEVEL_FILE = logging.DEBUG    # Detaillierter Level für die Log-Datei

# Konfiguriere das Root-Logger
def configure_logging(log_file_path=None, console_level=None, file_level=None):
    """
    Konfiguriert das zentrale Logging-System mit Ausgabe auf Konsole und in Datei.
    
    Args:
        log_file_path: Pfad zur Log-Datei (optional)
        console_level: Log-Level für die Konsolenausgabe (optional)
        file_level: Log-Level für die Dateiausgabe (optional)
    """
    if log_file_path is None:
        log_file_path = Path(__file__).parents[2] / "output_log.txt"
    
    if console_level is None:
        console_level = LOG_LEVEL_CONSOLE
        
    if file_level is None:
        file_level = LOG_LEVEL_FILE
    
    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Niedrigstes Level für den Root-Logger
    
    # Lösche alle vorhandenen Handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatter für Konsole und Datei
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Konsolen-Handler einrichten
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    
    # Datei-Handler einrichten
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    
    # Handler dem Root-Logger hinzufügen
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Spezielle Filter für DWD-Module einrichten
    wetterdienst_logger = logging.getLogger('wetterdienst')
    wetterdienst_logger.setLevel(logging.WARNING)
    
    dwd_logger = logging.getLogger('src.data_handlers.dwd_weather')
    dwd_logger.setLevel(logging.INFO)
    
    # Nachricht ausgeben, dass das Logging initialisiert wurde
    logging.info(f"Logging konfiguriert - Dateiausgabe nach: {log_file_path}")

# Filter-Klasse für DWD-Station-Informationen
class DWDStationFilter(logging.Filter):
    """
    Filtert Logging-Nachrichten, um nur die wichtigen DWD-Station-Informationen durchzulassen.
    """
    def filter(self, record):
        # Lasse nur bestimmte Nachrichten durch
        if "Verwende DWD-Station:" in record.msg:
            return True
        if "Stationen aus lokaler Datei geladen" in record.msg:
            return True
        return False
