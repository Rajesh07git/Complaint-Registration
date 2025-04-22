import pandas as pd
import re
import pickle
import nltk
import time
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt


# Download required NLP resources
nltk.download("stopwords")
nltk.download("punkt")
nltk.download('punkt_tab')
nltk.download("wordnet")


# Load dataset
dataset_path = "../datasets/new_dataset.csv"
df = pd.read_csv(dataset_path)

# Remove NaN values
df.dropna(subset=["Description of the Issue", "Type of Complaint"], inplace=True)
# Encode complaint categories
label_encoder = LabelEncoder()
y= label_encoder.fit_transform(df["Type of Complaint"])

# Initialize NLP tools
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()
# Text preprocessing function
def preprocess_text(text):
    text = text.lower()  # Lowercase conversion
    text = re.sub(r"[^a-zA-Z\s]", "", text)  # Remove special characters
    words = word_tokenize(text)  # Tokenization
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]  # Lemmatization & Stopword removal
    return " ".join(words)
# Apply preprocessing
X = df["Description of the Issue"].apply(preprocess_text)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# TF-IDF Vectorization
tfidf_vectorizer = TfidfVectorizer(
    max_features=7000, ngram_range=(1, 2), sublinear_tf=True, stop_words="english"
)
X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
X_test_tfidf = tfidf_vectorizer.transform(X_test)
# Define models
models = {
    "Logistic Regression": LogisticRegression(solver="liblinear", C=1.0),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "SVM": SVC(kernel="linear", C=1.0),
    "Naive Bayes": MultinomialNB(),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "Decision Tree": DecisionTreeClassifier(random_state=42)
}

# Train & Evaluate models
best_model = None
best_accuracy = 0
model_performance = {}
    
for model_name, model in models.items():
    print(f"Training {model_name}...")
    start_time = time.time()
    model.fit(X_train_tfidf, y_train)
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    end_time = time.time()
    
    model_performance[model_name] = {
        "accuracy": accuracy,
        "training_time": end_time - start_time
    }
    
    print(f"{model_name} Accuracy: {accuracy:.4f} | Training Time: {end_time - start_time:.2f} seconds")  
    
    # Save the best model
    if accuracy > best_accuracy:
        best_accuracy = accuracy
        best_model = model
        
    # Classification report
    print(f"Classification Report for {model_name}:\n", classification_report(y_test, y_pred))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=model.classes_, yticklabels=model.classes_)
    plt.title(f"Confusion Matrix - {model_name}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.show()

    # Cross-validation scores
    X_all_vec = tfidf_vectorizer.transform(X)  # Use full dataset vectorized
    cv_scores = cross_val_score(model, X_all_vec, y, cv=5)
    print(f"Cross-validation scores for {model_name}: {cv_scores}")
    print(f"Mean CV accuracy for {model_name}: {cv_scores.mean()}")
