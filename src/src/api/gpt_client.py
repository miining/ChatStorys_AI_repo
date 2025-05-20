from typing import Dict, List
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

class GPTClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.api_key

    def chat_session(self, prompt: str, user_message: str, messages: List[Dict]) -> str:
        """
        Generate novel content using GPT-4
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating novel content: {str(e)}")

    def summarize_chapter(self, content: str) -> str:
        """
        Generate a summary of the chapter
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional editor."},
                    {"role": "user", "content": f"Please summarize this chapter:\n\n{content}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error summarizing chapter: {str(e)}")

    def generate_outline(self, genre: str, requirements: Dict) -> str:
        """
        Maintain a chat session with GPT-4
        """
        try:
            prompt = f"Create a detailed outline for a {genre} novel. Consider these requirements: {requirements}"
            messages = [
                SystemMessage(content="You are a professional novelist. Create a detailed chapter outline."),
                HumanMessage(content=prompt)
            ]
            response = self.model(messages)
            return response.content
        except Exception as e:
            raise Exception(f"Error generating outline: {str(e)}")

    def format_response(self, response: str) -> Dict:
        """
        Format the model's response into a structured format
        """
        return {
            "content": response,
            "status": "success"
        } 