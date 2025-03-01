import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# # Download NLTK data files (run once)
# nltk.download("stopwords")
# nltk.download("punkt")
# nltk.download("punkt_tab")
# nltk.download("wordnet")

def preprocess_text(text):
    """Cleans and preprocesses text for TF-IDF similarity computation."""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and special characters
    text = re.sub(r"[^\w\s]", "", text)
    
    # Tokenize words
    words = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = [word for word in words if word not in stop_words]
    
    # Lemmatization (convert words to base form)
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]
    
    # Return cleaned text
    return " ".join(words)


def compute_tf_idf_similarity(text1, text2):
    """Computes TF-IDF cosine similarity after preprocessing."""
    # Preprocess both texts
    text1_clean = preprocess_text(text1)
    text2_clean = preprocess_text(text2)
    
    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1_clean, text2_clean])
    
    # Compute cosine similarity
    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return similarity
