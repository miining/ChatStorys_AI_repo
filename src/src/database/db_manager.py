'''
We can use external DB
'''

from typing import Optional, List, Dict
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("MONGODB_URL")
        if not self.connection_string:
            raise ValueError("MongoDB connection string is required")
        
        self.client = MongoClient(self.connection_string)
        self.db = self.client.novel_db
        self.users = self.db.users
        self.books = self.db.books
        self.chapters = self.db.chapters
        self.chat_storage = self.db.chat_storage
        self.music = self.db.music

    def get_current_chapter_contents(self, book_id: str) -> Dict:
        """
        Get the current working chapter contents (workingFlag = True)
        Returns:
            {
                "chapter_info": {
                    "bookId": "book1",
                    "chapter_Num": "chapter_1",
                    "sumChapter": "요약",
                    "workingFlag": True,
                    "musicTitle": "노래 제목",
                    "composer": "작곡자"
                },
                "chat_contents": [
                    {"LLM_Model": "...", "User": "..."},
                    ...
                ]
            }
        """
        try:
            # Get current working chapter
            chapter = self.chapters.find_one({
                "bookId": book_id,
                "workingFlag": True
            })
            
            if not chapter:
                return None
                
            # Get chat contents
            chat = self.chat_storage.find_one({
                "chapter_Num": chapter["chapter_Num"]
            })
            
            # Remove MongoDB _id
            if chapter:
                chapter.pop("_id", None)
            
            return {
                "chapter_info": chapter,
                "chat_contents": chat.get("content", []) if chat else []
            }
        except Exception as e:
            raise Exception(f"Error getting current chapter contents: {str(e)}")

    def get_completed_chapters_contents(self, book_id: str) -> List[Dict]:
        """
        Get contents of all completed chapters (workingFlag = False)
        Returns:
            [
                {
                    "chapter_info": {...},
                    "chat_contents": [...]
                },
                ...
            ]
        """
        try:
            # Get all completed chapters
            chapters = list(self.chapters.find(
                {
                    "bookId": book_id,
                    "workingFlag": False
                },
                {"_id": 0}
            ).sort("chapter_Num", 1))
            
            result = []
            for chapter in chapters:
                # Get chat contents for each chapter
                chat = self.chat_storage.find_one({
                    "chapter_Num": chapter["chapter_Num"]
                })
                
                result.append({
                    "chapter_info": chapter,
                    "chat_contents": chat.get("content", []) if chat else []
                })
            
            return result
        except Exception as e:
            raise Exception(f"Error getting completed chapters contents: {str(e)}")

    def get_user_data(self, user_id: str) -> Dict:
        """
        Get user's data including book and chapters
        """
        try:
            user = self.users.find_one({"userId": user_id})
            if not user:
                return None
            
            book = self.books.find_one({"userId": user_id})
            if not book:
                return {
                    "user": user,
                    "book": None,
                    "chapters": []
                }
            
            chapters = list(self.chapters.find(
                {"userId": user_id, "bookId": book["bookId"]},
                {"_id": 0}
            ).sort("chapter_Num", 1))
            
            return {
                "user": user,
                "book": book,
                "chapters": chapters
            }
        except Exception as e:
            raise Exception(f"Error getting user data: {str(e)}")

    def save_chapter(self, user_id: str, book_id: str, chapter_data: Dict) -> str:
        """
        Save chapter data to database
        """
        try:
            # Set workingFlag to True for new chapter
            chapter_data.update({
                "userId": user_id,
                "bookId": book_id,
                "workingFlag": True
            })
            
            # # Set workingFlag to False for all other chapters of this book
            # self.chapters.update_many(
            #     {
            #         "bookId": book_id,
            #         "workingFlag": True
            #     },
            #     {
            #         "$set": {"workingFlag": False}
            #     }
            # )
            
            result = self.chapters.insert_one(chapter_data)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error saving chapter: {str(e)}")

    def complete_chapter(self, book_id: str, chapter_num: str) -> bool:
        """
        Mark a chapter as completed by setting workingFlag to False
        """
        try:
            self.chapters.update_one(
                {
                    "bookId": book_id,
                    "chapter_Num": chapter_num
                },
                {
                    "$set": {"workingFlag": False}
                }
            )
            return True
        except Exception as e:
            raise Exception(f"Error completing chapter: {str(e)}")

    def update_chat_history(self, user_id: str, chapter_num: str, content: List[Dict]) -> bool:
        """
        Update chat history for a chapter
        """
        try:
            self.chat_storage.update_one(
                {
                    "userId": user_id,
                    "chapter_Num": chapter_num
                },
                {
                    "$set": {
                        "content": content
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            raise Exception(f"Error updating chat history: {str(e)}")

    def get_chat_history(self, user_id: str, chapter_num: str) -> Optional[List[Dict]]:
        """
        Get chat history for a chapter
        """
        try:
            chat = self.chat_storage.find_one({
                "userId": user_id,
                "chapter_Num": chapter_num
            })
            return chat.get("content", []) if chat else []
        except Exception as e:
            raise Exception(f"Error getting chat history: {str(e)}")

    def get_music_by_emotion(self, emotion_type: str) -> List[Dict]:
        """
        Get music recommendations based on emotion type
        """
        try:
            music_list = list(self.music.find(
                {"감정 type": emotion_type},
                {"_id": 0}
            ))
            return music_list
        except Exception as e:
            raise Exception(f"Error getting music recommendations: {str(e)}")

    def update_chapter_music(self, user_id: str, book_id: str, chapter_num: str, music_data: Dict) -> bool:
        """
        Update music information for a chapter
        """
        try:
            self.chapters.update_one(
                {
                    "userId": user_id,
                    "bookId": book_id,
                    "chapter_Num": chapter_num
                },
                {
                    "$set": {
                        "musicTitle": music_data.get("musicTitle"),
                        "composer": music_data.get("composer")
                    }
                }
            )
            return True
        except Exception as e:
            raise Exception(f"Error updating chapter music: {str(e)}") 