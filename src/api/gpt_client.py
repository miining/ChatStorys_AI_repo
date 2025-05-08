from typing import Dict, List
import openai
from dotenv import load_dotenv
import os

load_dotenv()

class GPTClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.api_key

    async def generate_novel_content(self, prompt: str, context: Dict) -> str:
        """
        Generate novel content using GPT-4
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative novelist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating novel content: {str(e)}")

    async def summarize_chapter(self, chapter_content: str) -> str:
        """
        Generate a summary of the chapter
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional editor."},
                    {"role": "user", "content": f"Please summarize this chapter:\n\n{chapter_content}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error summarizing chapter: {str(e)}")

    async def chat_session(self, messages: List[Dict]) -> str:
        """
        Maintain a chat session with GPT-4
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error in chat session: {str(e)}") 