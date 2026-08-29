import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


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


# Train model
print("Training model...")

model.fit(X, y)


# Save trained model
MODEL_PATH = "agent/data/ticket_classifier.joblib"

joblib.dump(model, MODEL_PATH)


print("Model trained successfully!")
print(f"Model saved as: {MODEL_PATH}")
print(f"Training samples: {len(df)}")
print(f"Categories: {sorted(y.unique())}")