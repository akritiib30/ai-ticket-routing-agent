import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


# Load dataset
df = pd.read_csv("tickets.csv")

# Combine title + description
df["text"] = (
    df["title"].fillna("")
    + " "
    + df["description"].fillna("")
)

# Input and target
X_text = df["text"]
y = df["category"]

# Split dataset
X_train_text, X_test_text, y_train, y_test = train_test_split(
    X_text,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# TF-IDF
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    max_features=5000
)

X_train = vectorizer.fit_transform(X_train_text)
X_test = vectorizer.transform(X_test_text)

# Train model
model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)

print("\n===== MODEL EVALUATION =====")
print(f"Test samples: {len(y_test)}")
print(f"Accuracy: {accuracy:.2%}")

print("\n===== CLASSIFICATION REPORT =====")
print(classification_report(y_test, y_pred))