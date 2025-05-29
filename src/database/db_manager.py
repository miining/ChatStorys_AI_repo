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
        # 환경변수에서 MongoDB 연결 문자열 가져오기
        self.connection_string = connection_string or os.getenv("MONGODB_URL")
        if not self.connection_string:
            raise ValueError("MongoDB connection string is required. Please set MONGODB_URL environment variable.")
        
        # MongoDB 연결 설정 개선
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5초 타임아웃
                connectTimeoutMS=10000,  # 10초 연결 타임아웃
                retryWrites=True
            )
            # 연결 테스트
            self.client.admin.command('ping')
        except Exception as e:
            raise Exception(f"Failed to connect to MongoDB: {str(e)}")
        
        # 데이터베이스 이름을 환경변수에서 가져오거나 기본값 사용
        db_name = os.getenv("MONGODB_DATABASE", "novel_db")
        self.db = self.client[db_name]
        
        # 컬렉션 초기화
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
            # 여러 가능한 필드명으로 검색 시도
            music_list = list(self.music.find(
                {
                    "$or": [
                {"감정 type": emotion_type},
                        {"emotion_type": emotion_type},
                        {"emotion": emotion_type}
                    ]
                },
                {"_id": 0}
            ))
            return music_list
        except Exception as e:
            raise Exception(f"Error getting music recommendations: {str(e)}")

    def get_all_music_with_features(self) -> List[Dict]:
        """
        Get all music from database with feature vectors for Algorithm 1
        Returns music documents that should include:
        - songName or musicTitle: 음악 제목
        - artist or composer: 아티스트/작곡가
        - feature_vector: [acoustic, electronic, aggressive, relaxed, happy, sad, party] 7차원 벡터
        """
        try:
            # 모든 음악 데이터 조회
            music_list = list(self.music.find({}, {"_id": 0}))
            
            # feature_vector가 없는 음악들을 위한 처리
            processed_music = []
            for music in music_list:
                # 기본 필드 확인 및 정규화
                processed_music_item = {
                    "songName": music.get("musicTitle", music.get("songName", "Unknown")),
                    "artist": music.get("composer", music.get("artist", "Unknown")),
                    "feature_vector": music.get("feature_vector", [0.5] * 7),  # 기본값: 중간값
                    "original_data": music  # 원본 데이터 보존
                }
                
                # feature_vector가 올바른 형식인지 확인
                if not isinstance(processed_music_item["feature_vector"], list) or len(processed_music_item["feature_vector"]) != 7:
                    # 감정 정보가 있으면 해당 감정의 특성 벡터 사용
                    emotion = music.get("emotion", music.get("감정 type", music.get("emotion_type", "joy")))
                    processed_music_item["feature_vector"] = self._get_default_feature_vector(emotion)
                
                processed_music.append(processed_music_item)
            
            return processed_music
        except Exception as e:
            raise Exception(f"Error getting all music with features: {str(e)}")

    def _get_default_feature_vector(self, emotion: str) -> List[float]:
        """
        감정에 따른 기본 특성 벡터 반환 (Algorithm 4와 동일한 매핑)
        """
        emotion_features = {
            'anger': [0.14, 0.86, 0.95, 0.05, 0.25, 0.75, 0.20],
            'sadness': [0.82, 0.18, 0.14, 0.86, 0.05, 0.95, 0.05],
            'anxiety': [0.22, 0.78, 0.92, 0.08, 0.17, 0.83, 0.10],
            'hurt': [0.75, 0.25, 0.20, 0.80, 0.13, 0.88, 0.05],
            'embarrassment': [0.33, 0.67, 0.89, 0.11, 0.33, 0.67, 0.15],
            'joy': [0.50, 0.50, 0.09, 0.91, 0.95, 0.05, 0.90]
        }
        
        # 한국어 감정을 영어로 매핑
        korean_to_english = {
            '분노': 'anger',
            '슬픔': 'sadness',
            '불안': 'anxiety',
            '상처': 'hurt',
            '당황': 'embarrassment',
            '기쁨': 'joy'
        }
        
        # 감정 매핑 및 기본값 반환
        mapped_emotion = korean_to_english.get(emotion, emotion.lower())
        return emotion_features.get(mapped_emotion, emotion_features['joy'])

    def update_chapter_music(self, user_id: str, book_id: str, chapter_num: str, music_data: Dict) -> bool:
        """
        Update music information for a chapter
        """
        try:
            update_data = {
                "musicTitle": music_data.get("musicTitle", ""),
                "composer": music_data.get("composer", ""),
            }

            result = self.chapters.update_one(
                {
                    "userId": user_id,
                    "bookId": book_id,
                    "chapter_Num": chapter_num
                },
                {
                    "$set": update_data
                }
            )
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Error updating chapter music: {str(e)}")

    def get_chapter_contents(self, book_id: str, chapter_num: str) -> Dict:
        """
        Get specific chapter contents by book_id and chapter_num
        Returns:
            {
                "chapter_info": {
                    "bookId": "book1",
                    "chapter_Num": "chapter_1",
                    "sumChapter": "요약",
                    "workingFlag": True/False,
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
            # Get specific chapter
            chapter = self.chapters.find_one({
                "bookId": book_id,
                "chapter_Num": chapter_num
            })
            
            if not chapter:
                return None
                
            # Get chat contents
            chat = self.chat_storage.find_one({
                "chapter_Num": chapter_num
            })
            
            # Remove MongoDB _id
            if chapter:
                chapter.pop("_id", None)
            
            return {
                "chapter_info": chapter,
                "chat_contents": chat.get("content", []) if chat else []
            }
        except Exception as e:
            raise Exception(f"Error getting chapter contents: {str(e)}")

    def update_chapter_summary(self, user_id: str, book_id: str, chapter_num: str, summary: str) -> bool:
        """
        Update chapter summary (sumChapter field)
        """
        try:
            result = self.chapters.update_one(
                {
                    "userId": user_id,
                    "bookId": book_id,
                    "chapter_Num": chapter_num
                },
                {
                    "$set": {
                        "sumChapter": summary,
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Error updating chapter summary: {str(e)}")

    def get_user_books(self, user_id: str) -> List[Dict]:
        """
        Get all books for a user
        """
        try:
            books = list(self.books.find(
                {"userId": user_id},
                {"_id": 0}
            ))
            return books
        except Exception as e:
            raise Exception(f"Error getting user books: {str(e)}")

    def get_book_info(self, book_id: str) -> Dict:
        """
        Get book information by book_id
        """
        try:
            book = self.books.find_one(
                {"bookId": book_id},
                {"_id": 0}
            )
            return book
        except Exception as e:
            raise Exception(f"Error getting book info: {str(e)}")

    def create_new_chapter(self, user_id: str, book_id: str, chapter_num: str) -> str:
        """
        Create a new chapter
        """
        try:
            chapter_data = {
                "bookId": book_id,
                "chapter_Num": chapter_num,
                "userId": user_id,
                "sumChapter": "",
                "workingFlag": True,
                "musicTitle": "",
                "composer": "",
                "created_at": datetime.now()
            }
            
            # Set other chapters' workingFlag to False
            self.chapters.update_many(
                {
                    "bookId": book_id,
                    "workingFlag": True
                },
                {
                    "$set": {"workingFlag": False}
                }
            )
            
            result = self.chapters.insert_one(chapter_data)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error creating new chapter: {str(e)}")

    def get_all_chapters_for_book(self, book_id: str) -> List[Dict]:
        """
        Get all chapters for a specific book
        """
        try:
            chapters = list(self.chapters.find(
                {"bookId": book_id},
                {"_id": 0}
            ).sort("chapter_Num", 1))
            return chapters
        except Exception as e:
            raise Exception(f"Error getting chapters for book: {str(e)}")

    def update_user_books(self, user_id: str, book_id: str) -> bool:
        """
        Add book_id to user's bookID array
        """
        try:
            result = self.users.update_one(
                {"userId": user_id},
                {
                    "$addToSet": {
                        "bookID": book_id
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Error updating user books: {str(e)}")

    def create_new_book(self, book_id: str, title: str, genre: str, user_id: str) -> str:
        """
        Create a new book
        """
        try:
            book_data = {
                "bookId": book_id,
                "title": title,
                "genre": genre,
                "userId": user_id,
                "created_at": datetime.now()
            }
            
            result = self.books.insert_one(book_data)
            
            # Add book_id to user's bookID array
            self.update_user_books(user_id, book_id)
            
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error creating new book: {str(e)}")

    def create_user(self, user_id: str, name: str, password: str) -> str:
        """
        Create a new user
        """
        try:
            user_data = {
                "userId": user_id,
                "name": name,
                "password": password,
                "bookID": [],
                "created_at": datetime.now()
            }
            
            result = self.users.insert_one(user_data)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")

    def get_user_by_id(self, user_id: str) -> Dict:
        """
        Get user by user_id
        """
        try:
            user = self.users.find_one(
                {"userId": user_id},
                {"_id": 0}
            )
            return user
        except Exception as e:
            raise Exception(f"Error getting user: {str(e)}")

    def verify_user_login(self, user_id: str, password: str) -> bool:
        """
        Verify user login credentials
        """
        try:
            user = self.users.find_one({
                "userId": user_id,
                "password": password
            })
            return user is not None
        except Exception as e:
            raise Exception(f"Error verifying user login: {str(e)}")

    def save_music_data(self, music_data: Dict) -> str:
        """
        Save music data to database
        """
        try:
            result = self.music.insert_one(music_data)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Error saving music data: {str(e)}")

    def delete_chapter(self, user_id: str, book_id: str, chapter_num: str) -> bool:
        """
        Delete a chapter and its chat history
        """
        try:
            # Delete chapter
            chapter_result = self.chapters.delete_one({
                "userId": user_id,
                "bookId": book_id,
                "chapter_Num": chapter_num
            })
            
            # Delete associated chat history
            chat_result = self.chat_storage.delete_one({
                "userId": user_id,
                "chapter_Num": chapter_num
            })
            
            return chapter_result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Error deleting chapter: {str(e)}")

    def delete_book(self, user_id: str, book_id: str) -> bool:
        """
        Delete a book and all its chapters and chat histories
        """
        try:
            # Get all chapters for the book
            chapters = self.get_all_chapters_for_book(book_id)
            
            # Delete all chapters and their chat histories
            for chapter in chapters:
                self.delete_chapter(user_id, book_id, chapter["chapter_Num"])
            
            # Delete the book
            book_result = self.books.delete_one({
                "bookId": book_id,
                "userId": user_id
            })
            
            # Remove book_id from user's bookID array
            self.users.update_one(
                {"userId": user_id},
                {
                    "$pull": {
                        "bookID": book_id
                    }
                }
            )
            
            return book_result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Error deleting book: {str(e)}")

    def get_statistics(self, user_id: str) -> Dict:
        """
        Get user statistics (books count, chapters count, etc.)
        """
        try:
            # Count books
            books_count = self.books.count_documents({"userId": user_id})
            
            # Count chapters
            chapters_count = self.chapters.count_documents({"userId": user_id})
            
            # Count completed chapters
            completed_chapters = self.chapters.count_documents({
                "userId": user_id,
                "workingFlag": False
            })
            
            # Count working chapters
            working_chapters = self.chapters.count_documents({
                "userId": user_id,
                "workingFlag": True
            })
            
            return {
                "books_count": books_count,
                "total_chapters": chapters_count,
                "completed_chapters": completed_chapters,
                "working_chapters": working_chapters,
                "completion_rate": completed_chapters / chapters_count if chapters_count > 0 else 0
            }
        except Exception as e:
            raise Exception(f"Error getting statistics: {str(e)}")

    def close_connection(self):
        """
        Close database connection
        """
        try:
            if self.client:
                self.client.close()
        except Exception as e:
            print(f"Error closing database connection: {str(e)}") 