import re
from typing import List, Dict
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

class TextProcessor:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
        
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        """
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        """
        return sent_tokenize(text)

    def tokenize_words(self, text: str) -> List[str]:
        """
        Split text into words
        """
        return word_tokenize(text)

    def remove_stopwords(self, words: List[str]) -> List[str]:
        """
        Remove stopwords from word list
        """
        return [word for word in words if word.lower() not in self.stop_words]

    def lemmatize_words(self, words: List[str]) -> List[str]:
        """
        Lemmatize words to their base form
        """
        return [self.lemmatizer.lemmatize(word) for word in words]

    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Extract key words from text
        """
        # Clean and tokenize text
        cleaned_text = self.clean_text(text)
        words = self.tokenize_words(cleaned_text)
        
        # Remove stopwords and lemmatize
        words = self.remove_stopwords(words)
        words = self.lemmatize_words(words)
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:num_keywords]]

    def calculate_readability_score(self, text: str) -> float:
        """
        Calculate text readability score using Flesch Reading Ease
        """
        sentences = self.tokenize_sentences(text)
        words = self.tokenize_words(text)
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        syllables = sum(self._count_syllables(word) for word in words)
        avg_syllables_per_word = syllables / len(words)
        
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0.0, min(100.0, score))

    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word
        """
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        previous_is_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_is_vowel:
                count += 1
            previous_is_vowel = is_vowel
        
        if word.endswith('e'):
            count -= 1
        return max(1, count)

    def analyze_text_metrics(self, text: str) -> Dict:
        """
        Analyze various text metrics
        """
        sentences = self.tokenize_sentences(text)
        words = self.tokenize_words(text)
        
        return {
            "sentence_count": len(sentences),
            "word_count": len(words),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "readability_score": self.calculate_readability_score(text),
            "keywords": self.extract_keywords(text)
        } 