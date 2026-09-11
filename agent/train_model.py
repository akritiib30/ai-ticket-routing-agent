import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


# Load dataset
DATA_PATH = "agent/data/tickets.csv"

df = pd.read_csv(DATA_PATH)

# Combine title and description
X = (
    df["title"].fillna("")
    + " "
    + df["description"].fillna("")
)

y = df["category"]


# Create ML pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=10000
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000
        )
    )
])


print("Training model...")


# Split data for evaluation when possible.
# Stratification keeps category proportions balanced.
try:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print(f"Validation accuracy: {accuracy:.2%}")
    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

except ValueError as exc:
    # Fall back to training on the complete dataset if the dataset
    # is too small for a reliable stratified split.
    print(f"Validation split skipped: {exc}")
    print("Training on the complete dataset instead.")

    model.fit(X, y)


# Save trained model
MODEL_PATH = "agent/data/ticket_classifier.joblib"

joblib.dump(model, MODEL_PATH)


print("\nModel trained successfully!")
print(f"Model saved as: {MODEL_PATH}")
print(f"Training samples: {len(df)}")
print(f"Categories: {sorted(y.unique())}")