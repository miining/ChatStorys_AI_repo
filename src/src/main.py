from typing import Dict, List, Optional
from .api.gpt_client import GPTClient
from .api.rag_client import RAGClient
from .database.db_manager import DatabaseManager
from .utils.prompt_templates import PromptTemplates
from .utils.text_processor import TextProcessor
from .utils.emotion_analyzer import EmotionAnalyzer
from .utils.music_recommender import MusicRecommender
import os
from dotenv import load_dotenv

# Add Redis Queue imports
import redis
from rq import Queue

load_dotenv()

# Setup Redis connection and queue
redis_conn = redis.Redis()
q = Queue(connection=redis_conn)

class NovelProcessor:
    def __init__(self):
        self.gpt_client = GPTClient()
        self.rag_client = RAGClient()
        self.db_manager = DatabaseManager()
        self.text_processor = TextProcessor()
        self.emotion_analyzer = EmotionAnalyzer()
        self.music_recommender = MusicRecommender()

    def generate_chapter(self, user_id: str, user_message: str, book_id: str) -> Dict:
        """
        description:
            
            사용자가 generate_chapter 메서드를 호출하면 다음과 같은 일련의 작업이 수행됩니다.

        parameters:
            
            user_id: 사용자의 고유 식별자
            user_message: 사용자의 메시지
            book_id: 사용자의 책의 고유 식별자

        prior condition (해당 메서드를 실행하기 전에 다음과 같은 요소들이 수행되어있어야 합니다):
            
            - 사용자(user_id)에 대한 DB 데이터가 존재해야합니다. 
                
                예를 들어 가장 처음 소설을 시작하는 경우,
                    user collection은 물론 book collection, chapter collection, chat_storage collection이 존재하긴 해야합니다.
                    user_id에 해당하는 DB가 없어서 발생하는 오류는 처리하지 않았습니다.

                예를 들어 한 권의 책을 이미 작성완료한 후 다른 새로운 책을 작성하려는 경우,
                    user collection에 존재하는 book에 새로운 book id가 추가되며 이를 parameter로 받습니다.
                    새롭게 만들어지는 book id에 대한 book collection, chapter collection, chat_storage collection가 존재해야합니다.

            - 현재 사용중인 chapter를 제외하고는 workingFlag가 False여야합니다.
                현재 이 코드는 해당 부분을 처리하지 않았습니다.

        steps:
            
            1. 사용자의 이전 contents를 DB에서 가져옵니다.
                1.1 fix me:
                    user data에서 book은 list로 존재합니다(DB schema 수정 필요 2025-05-13)
                    따라서 해당 책이나 챕터에 대한 정보를 DB에서 가져오는 부분(db_manager.py에서 get_user_data 메서드 참고)을 스키마에 맞게 수정해야합니다.
                    또한 해당 책에 대한 정보를 가져오는 부분이 없기 때문에 해당 부분도 수정해야합니다.
            
            2. 사용자의 이전 contents를 통해 현재 챕터의 컨텍스트를 생성합니다.
            
            3. 현재 챕터의 컨텍스트와 사용자의 메시지를 결합하여 GPT에 전달합니다.
                3.1 fix me:
                    gpt prompt 생성할때 rag를 통해 genre에 대한 requirement를 추가하는 부분이 존재하지 않음
                    rag_client와 prompt_templates.py에 있는 get_genre_prompt 함수를 활용하여 해당 기능을 추가해야함
            
            4. GPT의 응답을 받아 새로운 챕터를 생성합니다.
            
            5. 생성된 챕터를 DB에 저장합니다.
                5.1 check me:
                    지금의 코드는 chat_storage에 대해서만 update를 수행합니다. 따라서 해당 챕터에 대한 정보들과, 종료 등 다양한
                    DB 데이터의 update는 recommandate_music 메서드에서 수행해야합니다.
            
            6. 생성된 챕터를 반환합니다.       
            Return:
                {
                    "status": "success",
                    "chapter": chapter_data = 
                        {
                            "chapter_Num": chapter_num,
                            "userId": user_id,
                            "content": {"LLM_Model": content, "User": user_message},
                            "workingFlag": True
                        }
                }
            Error Returns:
                {
                    "status": "error",
                    "message": str(error_message)
                }
        """
        try:
            # Get user's previous content from DB
            user_data = self.db_manager.get_user_data(user_id)
            if not user_data or not user_data.get('book'):
                return {
                    "status": "error",
                    "message": "User or book not found"
                }

            book = user_data['book']
            book_id = book.get('bookId', '')
            # Get previous chapters contents
            previous_chapters = self.db_manager.get_completed_chapters_contents(book_id=book_id)
            
            # Get chat history for the chapter
            current_chapter = self.db_manager.get_current_chapter_contents(book_id=book_id)
            
            chat_history = current_chapter.get('chat_contents', [])
            
            # Convert chat history to continuous text with user responses
            continuous_text = ""
            for chat in chat_history:
                # 사용자 답변과 LLM 응답을 모두 포함
                if "User" in chat:
                    continuous_text += f"User: {chat['User']}\n"
                if "LLM_Model" in chat:
                    continuous_text += f"Assistant: {chat['LLM_Model']}\n"
            
            # Create context from previous chapters
            context = {
                "previous_chapters": "\n".join([
                    ch["chapter_info"].get('sumChapter', '') for ch in previous_chapters
                ]),
                "current_chapter": continuous_text,
                "book_title": book.get('title', ''),
                "book_genre": book.get('genre', ''),
            }
            
            # Generate chapter prompt
            chapter_num = current_chapter.get('chapter_info', {}).get('chapter_Num', '')
            prompt = PromptTemplates.get_chapter_prompt(chapter_num=chapter_num, context=context)
            
            # Generate content using GPT
            content = self.gpt_client.chat_session(prompt, user_message)
            
            # Create chapter data
            chapter_data = {
                "chapter_Num": chapter_num,
                "userId": user_id,
                "content": {"LLM_Model": content, "User": user_message},
                "workingFlag": True
            }
            
            # Update chat history
            chat_history = current_chapter.get('chat_contents', [])
            chat_history.append({"LLM_Model": content, "User": user_message})
            self.db_manager.update_chat_history(user_id, chapter_num, chat_history)
            
            return {
                "status": "success",
                "chapter": chapter_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def recommendate_music(self, user_id: str, book_id: str) -> Dict:
        """
        description:
            사용자가 recommendate_music 메서드를 호출하면 다음과 같은 일련의 작업이 수행됩니다.
            또한 음악을 추천한다는 것은 해당 챕터가 종료되었다는 의미입니다. 따라서 chapter의 workingFlag를 False로 변경합니다.

        parameters:
            user_id: 사용자의 고유 식별자
            book_id: 사용자의 책의 고유 식별자

        steps:
            1. 사용자의 이전 contents를 DB에서 가져옵니다.

            2. 사용자의 이전 contents를 통해 현재 챕터의 컨텍스트를 생성합니다.
            
            3. 현재 챕터의 컨텍스트를 통해 사용자의 감정을 분석합니다.
                3.1 need to add:
                    emotion_analyzer.py에서 사용자의 감정을 분석하는 부분이 존재하지 않음.
                    fine-tuning 된 모델을 활용하여 사용자의 감정을 분석해야합니다.
                    (KoELECTRA 모델 활용 예정)

            4. 사용자의 감정을 통해 음악을 추천합니다.
                4.1 need to add:
                    music_recommender.py에서 사용자의 감정을 통해 음악을 추천하는 부분이 존재하지 않음.
                    
            5. 추천된 음악을 DB에 저장합니다.
                5.1 need to add:
                    음악을 추천해준다는 것은 chapter가 종료되었다는 의미입니다.
                    따라서 해당 chapter에 대한 workingFlag를 False로 변경해야합니다.

            6. 추천된 음악을 반환합니다.
            Return:
                {
                    "status": "success",
                    "music": selected_music
                }
            Error Returns:
                {
                    "status": "error",
                    "message": str(error_message)
                }
        """
        try:
            # Get chapter contents from DB
            chapter_contents = self.db_manager.get_chapter_contents(book_id, chapter_num)
            if not chapter_contents:
                return {
                    "status": "error",
                    "message": "Chapter not found"
                }
            
            content = chapter_contents["chapter_info"].get('sumChapter', '')
            
            # Analyze emotions using KoELECTRA
            emotions = self.emotion_analyzer.analyze_emotions(content)
            
            # Get music recommendations based on emotions
            music_list = self.db_manager.get_music_by_emotion(emotions.get('dominant_emotion', ''))
            
            if music_list:
                # Select first music from the list
                selected_music = music_list[0]
                
                # Update chapter with music information
                self.db_manager.update_chapter_music(
                    user_id=user_id,
                    book_id=book_id,
                    chapter_num=chapter_num,
                    music_data={
                        "musicTitle": selected_music.get('musicTitle'),
                        "composer": selected_music.get('composer')
                    }
                )
                
                return {
                    "status": "success",
                    "music": selected_music
                }
            else:
                return {
                    "status": "error",
                    "message": "No music found for the emotion"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

def process_job(job_type: str, **kwargs) -> Dict:
    """
    Process jobs from the server
    """
    processor = NovelProcessor()
    
    if job_type == "generate_chapter":
        return processor.generate_chapter(
            user_id=kwargs.get('user_id'),
            user_message=kwargs.get('user_message'),
            book_id=kwargs.get('book_id')
        )
    elif job_type == "recommendate_music":
        return processor.recommendate_music(
            user_id=kwargs.get('user_id'),
            book_id=kwargs.get('book_id')
        )
    else:
        return {
            "status": "error",
            "message": f"Unknown job type: {job_type}"
        }

if __name__ == "__main__":
    # This will be called by the worker when processing jobs
    pass 