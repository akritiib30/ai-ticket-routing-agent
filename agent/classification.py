from pathlib import Path
import joblib

from .models import ClassificationResult


class Classifier:
    """
    ML-based ticket classifier.

    Loads the already-trained TF-IDF + Logistic Regression
    model from disk.
    """

    def __init__(self, seed_tickets=None):

        # Path to the saved trained model
        model_path = (
            Path(__file__).parent
            / "data"
            / "ticket_classifier.joblib"
        )

        # Check that the model exists
        if not model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at: {model_path}"
            )

        # Load the trained model
        self.model = joblib.load(model_path)

        # Get categories from the trained model
        self.categories = list(self.model.classes_)

    def predict(self, text: str) -> ClassificationResult:
        """
        Predict the category of a new ticket.
        """

        # Predict category
        predicted_category = self.model.predict([text])[0]

        # Get prediction probabilities
        probabilities = self.model.predict_proba([text])[0]

        # Highest probability = confidence
        confidence = float(max(probabilities))

        return ClassificationResult(
            category=predicted_category,
            confidence=confidence
        )