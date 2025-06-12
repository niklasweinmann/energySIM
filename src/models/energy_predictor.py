from typing import List, Optional, Tuple
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import pandas as pd

class EnergyPredictor:
    """Neuronales Netzwerk für Energiebedarfsvorhersagen."""
    
    def __init__(self):
        self.model: Optional[models.Sequential] = None
        self.feature_scaler = None
        self.target_scaler = None
        self.sequence_length = 24  # 24 Stunden Sequenzlänge
        
    def build_model(self, input_shape: Tuple[int, int]):
        """
        Erstellt die Architektur des neuronalen Netzwerks.
        
        Args:
            input_shape: Form der Eingabedaten (Zeitschritte, Features)
        """
        self.model = models.Sequential([
            # Bidirektionales LSTM für Zeitreihenanalyse
            layers.Bidirectional(
                layers.LSTM(64, return_sequences=True),
                input_shape=input_shape
            ),
            layers.Dropout(0.2),
            
            # Zweite LSTM-Schicht für tieferes Lernen
            layers.Bidirectional(layers.LSTM(32)),
            layers.Dropout(0.2),
            
            # Dense Layers für die Vorhersage
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dense(32, activation='relu'),
            layers.Dense(1)  # Vorhersage des Energiebedarfs
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
    
    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Bereitet Zeitreihen für das Training vor.
        
        Args:
            data: DataFrame mit Features und Zielvariable
            
        Returns:
            X: Sequenzen der Features
            y: Zielvariablen
        """
        sequences = []
        targets = []
        
        for i in range(len(data) - self.sequence_length):
            # Erstelle Sequenz der Länge sequence_length
            sequence = data.iloc[i:i + self.sequence_length]
            target = data.iloc[i + self.sequence_length]['energy_demand']
            
            sequences.append(sequence.values)
            targets.append(target)
            
        return np.array(sequences), np.array(targets)
    
    def train(self, 
             train_data: pd.DataFrame,
             validation_split: float = 0.2,
             epochs: int = 50,
             batch_size: int = 32):
        """
        Trainiert das Modell mit den gegebenen Daten.
        
        Args:
            train_data: DataFrame mit Trainingsdaten
            validation_split: Anteil der Validierungsdaten
            epochs: Anzahl der Trainingsepochen
            batch_size: Batch-Größe für das Training
        """
        # Daten vorbereiten
        X, y = self.prepare_sequences(train_data)
        
        # Early Stopping zur Vermeidung von Overfitting
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        
        # Training durchführen
        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping],
            verbose=1
        )
        
        return history
    
    def predict(self, input_sequence: np.ndarray) -> np.ndarray:
        """
        Macht eine Vorhersage für eine Eingabesequenz.
        
        Args:
            input_sequence: Sequenz der Eingabedaten
            
        Returns:
            Vorhersage des Energiebedarfs
        """
        if self.model is None:
            raise ValueError("Modell wurde noch nicht trainiert")
        
        # Reshape für die Vorhersage
        if len(input_sequence.shape) == 2:
            input_sequence = np.expand_dims(input_sequence, axis=0)
            
        return self.model.predict(input_sequence)
    
    def evaluate(self, test_data: pd.DataFrame) -> dict:
        """
        Evaluiert das Modell auf Testdaten.
        
        Args:
            test_data: DataFrame mit Testdaten
            
        Returns:
            Dictionary mit Evaluationsmetriken
        """
        X_test, y_test = self.prepare_sequences(test_data)
        
        # Modell evaluieren
        evaluation = self.model.evaluate(X_test, y_test, verbose=0)
        
        return {
            'loss': evaluation[0],
            'mae': evaluation[1]
        }
