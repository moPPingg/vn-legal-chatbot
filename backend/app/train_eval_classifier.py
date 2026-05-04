from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
import pandas as pd

# Import our tiny dataset and model
from app.classifier import TRAIN_DATA, train_classifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

def evaluate_model():
    print("Evaluating Law Classifier Metrics...")
    texts, labels = zip(*TRAIN_DATA)
    
    # 70/30 Train-Test split
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.3, random_state=42)
    
    # Train pipeline
    clf = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))),
        ("lr", LogisticRegression(max_iter=1000, C=5.0)),
    ])
    clf.fit(X_train, y_train)
    
    # Predict
    y_pred = clf.predict(X_test)
    
    print("\n" + "="*50)
    print("ACCURACY SCORE:")
    print("="*50)
    print(f"{accuracy_score(y_test, y_pred):.2f}")
    
    print("\n" + "="*50)
    print("CLASSIFICATION REPORT:")
    print("="*50)
    # zero_division=0 to suppress warnings for labels not in the split
    print(classification_report(y_test, y_pred, zero_division=0))
    
    print("\n" + "="*50)
    print("CONFUSION MATRIX:")
    print("="*50)
    labels_unique = sorted(list(set(y_test) | set(y_pred)))
    cm = confusion_matrix(y_test, y_pred, labels=labels_unique)
    cm_df = pd.DataFrame(cm, index=labels_unique, columns=labels_unique)
    print(cm_df)

if __name__ == "__main__":
    evaluate_model()
