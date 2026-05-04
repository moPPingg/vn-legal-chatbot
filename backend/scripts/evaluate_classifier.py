import sys
from pathlib import Path
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.classifier import TRAIN_DATA, MODEL_PATH

def evaluate():
    print("--- Evaluating Law Classifier ---")
    
    # Load data
    texts, labels = zip(*TRAIN_DATA)
    
    # Load model
    if not MODEL_PATH.exists():
        print(f"Error: Model file not found at {MODEL_PATH}. Run training first.")
        return
        
    with open(MODEL_PATH, "rb") as f:
        clf = pickle.load(f)
    
    # Predictions
    y_pred = clf.predict(list(texts))
    y_true = list(labels)
    
    # Calculate Metrics
    acc = accuracy_score(y_true, y_pred)
    print(f"\nOverall Accuracy: {acc:.2%}")
    
    print("\nDetailed Classification Report:")
    print(classification_report(y_true, y_pred))
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    classes = sorted(list(set(y_true)))
    
    print("\nConfusion Matrix:")
    print("Rows: True, Columns: Predicted")
    header = " " * 15 + " ".join([f"{c[:10]:>10}" for c in classes])
    print(header)
    for i, row in enumerate(cm):
        row_str = f"{classes[i][:15]:<15}" + " ".join([f"{val:>10}" for val in row])
        print(row_str)

    print("\n--- Evaluation Complete ---")

if __name__ == "__main__":
    evaluate()
