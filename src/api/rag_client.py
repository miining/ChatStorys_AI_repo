from typing import Dict, List
import faiss
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
import os
from dotenv import load_dotenv

load_dotenv()

class RAGClient:
    def __init__(self, model_path: str = None, openai_api_key: str = None):
        # 환경변수에서 API 키와 모델 경로 가져오기
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.model_path = model_path or os.getenv("VECTOR_STORE_PATH", "./vector_store")
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """
        Initialize the vector store with genre-specific data
        """
        try:
            if os.path.exists(self.model_path):
                self.vector_store = FAISS.load_local(self.model_path, self.embeddings)
            else:
                # Create new vector store if it doesn't exist
                self.vector_store = FAISS.from_texts([""], self.embeddings)
        except Exception as e:
            raise Exception(f"Error initializing vector store: {str(e)}")

    def search_genre_requirements(self, genre: str) -> Dict:
        """
        Search for genre-specific requirements and guidelines
        """
        try:
            query = f"Requirements and guidelines for writing {genre} novels"
            docs = self.vector_store.similarity_search(query, k=3)
            return {
                "genre": genre,
                "requirements": [doc.page_content for doc in docs]
            }
        except Exception as e:
            raise Exception(f"Error searching genre requirements: {str(e)}")

    def search_similar_chapters(self, query: str) -> List:
        """
        Search for similar chapters based on the query
        """
        try:
            docs = self.vector_store.similarity_search(query, k=3)
            return [doc.page_content for doc in docs]
        except Exception as e:
            raise Exception(f"Error searching similar chapters: {str(e)}")

    def format_search_results(self, results: List) -> str:
        """
        Format search results into a readable string
        """
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(f"Result {i}:\n{result}\n")
        return "\n".join(formatted_results)

    def update_vector_store(self, new_texts: List[str]):
        """
        Update the vector store with new texts
        """
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_text("\n".join(new_texts))
            self.vector_store.add_texts(texts)
            self.vector_store.save_local(self.model_path)
        except Exception as e:
            raise Exception(f"Error updating vector store: {str(e)}") 