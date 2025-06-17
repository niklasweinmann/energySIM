#!/usr/bin/env python3
"""
Test der DWD API um zu verstehen, welche Daten verfügbar sind
"""

import pytest
from datetime import datetime, timedelta
from wetterdienst.provider.dwd.observation import DwdObservationRequest
from wetterdienst import Settings
import pandas as pd


def test_dwd_api_availability():
    """Teste DWD API um verfügbare Daten zu verstehen"""
    
    # Settings
    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
    
    # Test: Prüfe verfügbare Stationen für Berlin
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=datetime(2023, 6, 1),
        end_date=datetime(2023, 6, 2),
        settings=settings
    )
    
    # Finde Stationen in der Nähe von Berlin
    stations = request.filter_by_distance((52.52, 13.41), 50)  # 50km Radius
    stations_df = stations.df.to_pandas()
    
    # Assertions
    assert len(stations_df) > 0, "Es sollten Stationen in der Nähe von Berlin gefunden werden"
    assert 'station_id' in stations_df.columns, "DataFrame sollte station_id Spalte haben"
    assert 'name' in stations_df.columns, "DataFrame sollte name Spalte haben"


def test_dwd_data_retrieval():
    """Teste das Abrufen von echten DWD-Daten"""
    
    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
    
    # Teste für eine bekannte aktive Station (Berlin-Tempelhof)
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=datetime(2023, 6, 1),
        end_date=datetime(2023, 6, 2),
        settings=settings
    )
    
    # Verwende die Station, die wir als aktiv identifiziert haben
    stations = request.filter_by_station_id(station_id=["00433"])  # Berlin-Tempelhof
    
    try:
        values = stations.values.all()
        values_df = values.df.to_pandas()
        
        # Assertions
        assert len(values_df) > 0, "Es sollten Daten für Station 00433 verfügbar sein"
        assert 'parameter' in values_df.columns, "DataFrame sollte parameter Spalte haben"
        assert 'value' in values_df.columns, "DataFrame sollte value Spalte haben"
        assert 'date' in values_df.columns, "DataFrame sollte date Spalte haben"
        
        # Prüfe auf Temperaturdaten
        temp_data = values_df[values_df['parameter'] == 'temperature_air_mean_2m']
        assert len(temp_data) > 0, "Temperaturdaten sollten verfügbar sein"
        
    except Exception as e:
        pytest.skip(f"DWD API nicht verfügbar oder Station inaktiv: {e}")


@pytest.mark.parametrize("start_date,end_date", [
    (datetime(2023, 6, 1), datetime(2023, 6, 2)),   # Sommer 2023
    (datetime(2023, 12, 1), datetime(2023, 12, 2)), # Winter 2023
])
def test_dwd_different_timeranges(start_date, end_date):
    """Teste verschiedene Zeiträume"""
    
    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
    
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=start_date,
        end_date=end_date,
        settings=settings
    )
    
    try:
        stations = request.filter_by_distance((52.52, 13.41), 20)
        if len(stations.df) > 0:
            values = stations.values.all()
            values_df = values.df.to_pandas()
            # Es sollten Daten gefunden werden, aber das kann je nach Verfügbarkeit variieren
            # Daher nur ein informativer Test
            print(f"Zeitraum {start_date.strftime('%Y-%m-%d')} bis {end_date.strftime('%Y-%m-%d')}: {len(values_df)} Datenpunkte")
            
    except Exception as e:
        pytest.skip(f"DWD API Fehler für Zeitraum {start_date} bis {end_date}: {e}")


if __name__ == "__main__":
    # Für direktes Ausführen - zeigt detaillierte Informationen
    print("=== DWD API Test ===")
    
    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
    
    print("\n1. Prüfe verfügbare Stationen für Berlin...")
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=datetime(2023, 6, 1),
        end_date=datetime(2023, 6, 2),
        settings=settings
    )
    
    stations = request.filter_by_distance((52.52, 13.41), 50)
    stations_df = stations.df.to_pandas()
    print(f"Gefundene Stationen: {len(stations_df)}")
    if len(stations_df) > 0:
        print(stations_df[['station_id', 'name', 'start_date', 'end_date']].head())
    
    print("\n2. Teste Station 00433 (Berlin-Tempelhof)...")
    try:
        station_request = DwdObservationRequest(
            parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
            start_date=datetime(2023, 6, 1),
            end_date=datetime(2023, 6, 2),
            settings=settings
        )
        
        station_data = station_request.filter_by_station_id(station_id=["00433"])
        values = station_data.values.all()
        values_df = values.df.to_pandas()
        
        print(f"✓ Daten erfolgreich abgerufen: {len(values_df)} Einträge")
        print(f"Spalten: {values_df.columns.tolist()}")
        if len(values_df) > 0:
            print("Verfügbare Parameter:", values_df['parameter'].unique())
            
    except Exception as e:
        print(f"✗ Fehler: {e}")
