"""
Tests für den EnergyPredictor.
"""

import unittest
import numpy as np
import pandas as pd
from src.models.energy_predictor import EnergyPredictor

class TestEnergyPredictor(unittest.TestCase):
    def setUp(self):
        """Test-Setup mit synthetischen Daten."""
        self.predictor = EnergyPredictor()
        
        # Synthetische Daten erstellen
        np.random.seed(42)
        dates = pd.date_range(start='2025-01-01', periods=1000, freq='H')
        
        # Features erstellen
        self.data = pd.DataFrame({
            'temperature': np.random.normal(20, 5, 1000),
            'humidity': np.random.normal(60, 10, 1000),
            'solar_radiation': np.abs(np.random.normal(500, 200, 1000)),
            'energy_demand': np.abs(np.random.normal(10, 2, 1000))
        }, index=dates)
        
    def test_model_building(self):
        """Test der Modellarchitektur."""
        input_shape = (24, 4)  # 24 Zeitschritte, 4 Features
        self.predictor.build_model(input_shape)
        
        # Überprüfe, ob Modell erstellt wurde
        self.assertIsNotNone(self.predictor.model)
        
        # Überprüfe Modellarchitektur
        expected_output_shape = (None, 1)  # Batch-Dimension, 1 Ausgabewert
        self.assertEqual(
            self.predictor.model.output_shape,
            expected_output_shape
        )
    
    def test_sequence_preparation(self):
        """Test der Sequenzvorbereitung."""
        X, y = self.predictor.prepare_sequences(self.data)
        
        # Überprüfe Dimensionen
        expected_sequence_length = self.predictor.sequence_length
        expected_features = len(self.data.columns)
        
        self.assertEqual(X.shape[1], expected_sequence_length)
        self.assertEqual(X.shape[2], expected_features)
        self.assertEqual(len(y.shape), 1)
    
    def test_training(self):
        """Test des Modelltrainings."""
        # Modell erstellen
        input_shape = (24, len(self.data.columns))
        self.predictor.build_model(input_shape)
        
        # Training mit wenigen Epochen
        history = self.predictor.train(
            self.data,
            epochs=2,
            batch_size=32
        )
        
        # Überprüfe Training
        self.assertIn('loss', history.history)
        self.assertIn('val_loss', history.history)
        
    def test_prediction(self):
        """Test der Vorhersage."""
        # Modell vorbereiten und trainieren
        input_shape = (24, len(self.data.columns))
        self.predictor.build_model(input_shape)
        self.predictor.train(self.data, epochs=2)
        
        # Testsequenz erstellen
        test_sequence = self.data.iloc[:24].values
        prediction = self.predictor.predict(test_sequence)
        
        # Überprüfe Vorhersageformat
        self.assertEqual(prediction.shape[-1], 1)
        self.assertTrue(np.all(np.isfinite(prediction)))

if __name__ == '__main__':
    unittest.main()
