from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# 프로젝트 내부 모듈 임포트
from .api.gpt_client import GPTClient
from .api.rag_client import RAGClient
from .database.db_manager import DatabaseManager
from .utils.prompt_templates import PromptTemplates
from .utils.text_processor import TextProcessor
from .utils.emotion_analyzer import EmotionAnalyzer
from .utils.music_recommender import MusicRecommender

# 환경변수 로드
load_dotenv()

class NovelProcessor:
    """소설 생성 및 처리를 담당하는 메인 클래스"""
    
    def __init__(self):
        """소설 처리에 필요한 모든 클라이언트 초기화"""
        self.gpt_client = GPTClient()
        self.rag_client = RAGClient()
        self.db_manager = DatabaseManager()
        self.text_processor = TextProcessor()
        self.emotion_analyzer = EmotionAnalyzer()
        self.music_recommender = MusicRecommender()

    def generate_chapter(self, user_id: str, user_message: str, book_id: str) -> Dict:
        """
        소설 챕터 생성 함수
        
        사용자의 입력을 받아 AI가 소설의 다음 내용을 생성합니다.
        이전 챕터들의 맥락과 현재 챕터의 채팅 히스토리를 모두 활용하여
        일관성 있는 스토리를 생성합니다.

        매개변수:
            user_id: 사용자의 고유 식별자
            user_message: 사용자가 입력한 메시지 (스토리 방향 지시)
            book_id: 현재 작성 중인 책의 고유 식별자

        반환값:
            성공 시: {"status": "success", "chapter": 챕터_데이터}
            실패 시: {"status": "error", "message": 오류_메시지}
        
        처리 과정:
            1. 사용자 존재 여부 및 책 정보 확인
            2. 이전 완료된 챕터들의 요약 정보 조회
            3. 현재 챕터의 채팅 히스토리 조회
            4. 컨텍스트 정보 구성 (이전 챕터 + 현재 진행상황)
            5. GPT를 이용한 소설 내용 생성
            6. 생성된 내용을 DB에 저장
            7. 결과 반환
        """
        try:
            # 1. 사용자 존재 여부 확인
            user = self.db_manager.get_user_by_id(user_id)
            if not user:
                return {
                    "status": "error",
                    "message": "사용자를 찾을 수 없습니다"
                }
            
            # 2. 책 정보 확인 (사용자가 해당 책에 접근 권한이 있는지 확인)
            book_info = self.db_manager.get_book_info(book_id)
            if not book_info:
                return {
                    "status": "error",
                    "message": "책 정보를 찾을 수 없습니다"
                }
            
            # 3. 사용자가 해당 책의 소유자인지 확인
            if book_info.get('userId') != user_id:
                return {
                    "status": "error",
                    "message": "해당 책에 대한 접근 권한이 없습니다"
                }
            
            # 4. 이전 완료된 챕터들의 내용 조회 (book_id 직접 사용)
            previous_chapters = self.db_manager.get_completed_chapters_contents(book_id=book_id)
            
            # 5. 현재 작업 중인 챕터의 채팅 히스토리 조회 (book_id 직접 사용)
            current_chapter = self.db_manager.get_current_chapter_contents(book_id=book_id)
            
            # 6. 현재 작업 중인 챕터가 없는 경우 처리
            if not current_chapter:
                return {
                    "status": "error",
                    "message": "현재 작업 중인 챕터가 없습니다. 새 챕터를 시작해주세요."
                }
            
            chat_history = current_chapter.get('chat_contents', [])
            
            # 7. 채팅 히스토리를 연속된 텍스트로 변환
            continuous_text = ""
            for chat in chat_history:
                if "User" in chat:
                    continuous_text += f"사용자: {chat['User']}\n"
                if "LLM_Model" in chat:
                    continuous_text += f"AI: {chat['LLM_Model']}\n"
            
            # 8. GPT에 전달할 컨텍스트 정보 구성
            context = {
                "previous_chapters": "\n".join([
                    ch["chapter_info"].get('sumChapter', '') for ch in previous_chapters
                ]),
                "current_chapter": continuous_text,
                "book_title": book_info.get('title', ''),
                "book_genre": book_info.get('genre', ''),
            }
            
            # 9. 현재 챕터 번호 확인
            chapter_num = current_chapter.get('chapter_info', {}).get('chapter_Num', '')
            
            # 10. GPT를 이용하여 소설 내용 생성 (개선된 chat_session 사용)
            content = self.gpt_client.chat_session(
                chapter_num=chapter_num,
                context=context,
                user_message=user_message,
                messages=chat_history  # 채팅 히스토리 전체 전달
            )
            
            # 11. 생성된 챕터 데이터 구성
            chapter_data = {
                "chapter_Num": chapter_num,
                "userId": user_id,
                "bookId": book_id,  # book_id 직접 사용
                "content": {"LLM_Model": content, "User": user_message},
                "workingFlag": True
            }
            
            # 12. 채팅 히스토리 업데이트
            updated_chat_history = current_chapter.get('chat_contents', [])
            updated_chat_history.append({"LLM_Model": content, "User": user_message})
            self.db_manager.update_chat_history(user_id, chapter_num, updated_chat_history)
            
            return {
                "status": "success",
                "chapter": chapter_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"소설 생성 중 오류가 발생했습니다: {str(e)}"
            }

    def finish_chapter_and_recommend_music(self, user_id: str, book_id: str) -> Dict:
        """
        챕터 완료 및 음악 추천 함수
        
        현재 작업 중인 챕터(workingFlag=True)의 내용을 요약하고 DB에 저장한 후,
        Algorithm 1을 사용하여 적절한 음악을 추천합니다.
        모든 처리가 완료되면 workingFlag를 False로 변경합니다.

        매개변수:
            user_id: 사용자의 고유 식별자
            book_id: 책의 고유 식별자

        반환값:
            성공 시: {"status": "success", "summary": 챕터_요약, "music": 음악_정보}
            실패 시: {"status": "error", "message": 오류_메시지}
            
        처리 과정:
            1. book_id로 현재 작업 중인 챕터 조회
            2. GPT를 통한 챕터 내용 요약 생성
            3. 챕터에 요약 정보 저장
            4. Algorithm 1을 이용한 음악 추천 (KoELECTRA + 코사인 유사도)
            5. 챕터에 음악 정보 저장 및 workingFlag를 False로 변경
            6. 요약 및 음악 정보 반환
        """
        try:
            # 1. book_id로 현재 작업 중인 챕터 조회
            current_chapter = self.db_manager.get_current_chapter_contents(book_id=book_id)
            if not current_chapter:
                return {
                    "status": "error",
                    "message": "현재 작업 중인 챕터가 없습니다"
                }
            
            chapter_num = current_chapter.get('chapter_info', {}).get('chapter_Num', '')
            if not chapter_num:
                return {
                    "status": "error",
                    "message": "챕터 번호를 찾을 수 없습니다"
                }
            
            # 2. 챕터의 채팅 내용을 하나의 연속된 텍스트로 변환
            chat_contents = current_chapter.get('chat_contents', [])
            chapter_content_text = ""
            
            for chat in chat_contents:
                if "User" in chat:
                    chapter_content_text += f"사용자: {chat['User']}\n"
                if "LLM_Model" in chat:
                    chapter_content_text += f"AI: {chat['LLM_Model']}\n"
            
            if not chapter_content_text.strip():
                return {
                    "status": "error",
                    "message": "챕터에 요약할 내용이 없습니다"
                }
            
            # 3. GPT를 통한 챕터 요약 생성
            try:
                chapter_summary = self.gpt_client.summarize_chapter(
                    content=chapter_content_text,
                    chapter_num=chapter_num
                )
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"챕터 요약 생성 중 오류가 발생했습니다: {str(e)}"
                }
            
            # 4. 챕터 요약 정보 업데이트
            try:
                self.db_manager.update_chapter_summary(
                    user_id=user_id,
                    book_id=book_id,
                    chapter_num=chapter_num,
                    summary=chapter_summary
                )
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"요약 DB 저장 중 오류가 발생했습니다: {str(e)}"
                }
            
            # 5. Algorithm 1을 사용한 음악 추천
            try:
                # 음악 데이터베이스 조회 (모든 음악)
                music_db = self.db_manager.get_all_music_with_features()
                
                if music_db and len(music_db) > 0:
                    # Algorithm 1: recommend_music 사용
                    recommendations = self.music_recommender.recommend_music(
                        userID=user_id,
                        novelContents=chapter_summary,  # 요약된 내용 사용
                        musicDB=music_db,
                        N=1  # 챕터당 하나의 음악 추천
                    )
                    
                    if recommendations and len(recommendations) > 0:
                        # 가장 유사도가 높은 음악 선택
                        selected_music = recommendations[0]
                        
                        # 6. 챕터에 음악 정보 저장 및 완료 처리
                        try:
                            self.db_manager.update_chapter_music(
                                user_id=user_id,
                                book_id=book_id,
                                chapter_num=chapter_num,
                                music_data={
                                    "musicTitle": selected_music.get('songName'),
                                    "composer": selected_music.get('artist'),
                                    "similarity": selected_music.get('similarity'),
                                    "emotion": selected_music.get('emotion')
                                }
                            )
                            
                            # 챕터 완료 처리 (workingFlag를 False로 변경)
                            self.db_manager.complete_chapter(book_id, chapter_num)
                            
                        except Exception as e:
                            return {
                                "status": "error",
                                "message": f"음악 정보 DB 저장 중 오류가 발생했습니다: {str(e)}"
                            }
                        
                        return {
                            "status": "success",
                            "summary": {
                                "content": chapter_summary,
                                "word_count": len(chapter_summary),
                                "generated_at": "현재 시간"
                            },
                            "music": {
                                "musicTitle": selected_music.get('songName'),
                                "composer": selected_music.get('artist'),
                                "similarity": selected_music.get('similarity'),
                                "emotion": selected_music.get('emotion'),
                                "recommendation_method": "Algorithm 1 (KoELECTRA + Cosine Similarity)"
                            },
                            "chapter_info": {
                                "chapter_num": chapter_num,
                                "completion_status": "completed",
                                "total_content_length": len(chapter_content_text),
                                "working_flag": False
                            }
                        }
                    else:
                        # 추천 결과가 없는 경우
                        raise Exception("음악 추천 결과가 없습니다")
                else:
                    # 음악 데이터베이스가 없는 경우
                    raise Exception("음악 데이터베이스를 찾을 수 없습니다")
                    
            except Exception as e:
                print(f"Algorithm 1 음악 추천 오류: {str(e)}")
                
                # 대안: 기존 방식으로 폴백
                try:
                    # KoELECTRA 모델을 이용한 감정 분석 (폴백)
                    emotions = self.emotion_analyzer.analyze_emotions(chapter_summary)
                    dominant_emotion = emotions.get('dominant_emotion', 'joy')
                    
                    # 주요 감정에 기반한 음악 추천 (기존 방식)
                    music_list = self.db_manager.get_music_by_emotion(dominant_emotion)
                    
                    if music_list:
                        selected_music = music_list[0]
                        
                        # 챕터에 음악 정보 저장하고 완료 처리
                        self.db_manager.update_chapter_music(
                            user_id=user_id,
                            book_id=book_id,
                            chapter_num=chapter_num,
                            music_data={
                                "musicTitle": selected_music.get('musicTitle'),
                                "composer": selected_music.get('composer'),
                            }
                        )
                        
                        self.db_manager.complete_chapter(book_id, chapter_num)
                        
                        return {
                            "status": "success",
                            "summary": {
                                "content": chapter_summary,
                                "word_count": len(chapter_summary),
                                "generated_at": "현재 시간"
                            },
                            "music": {
                                "musicTitle": selected_music.get('musicTitle'),
                                "composer": selected_music.get('composer'),
                                "emotion": dominant_emotion,
                                "recommendation_method": "Fallback (emotion-based)"
                            },
                            "chapter_info": {
                                "chapter_num": chapter_num,
                                "completion_status": "completed",
                                "total_content_length": len(chapter_content_text),
                                "working_flag": False
                            }
                        }
                    else:
                        # 음악을 찾을 수 없는 경우에도 요약은 저장하고 완료 처리
                        self.db_manager.complete_chapter(book_id, chapter_num)
                        
                        return {
                            "status": "partial_success",
                            "message": f"감정 '{dominant_emotion}'에 해당하는 음악을 찾을 수 없어 요약만 저장되었습니다",
                            "summary": {
                                "content": chapter_summary,
                                "word_count": len(chapter_summary),
                                "generated_at": "현재 시간"
                            },
                            "music": None,
                            "chapter_info": {
                                "chapter_num": chapter_num,
                                "completion_status": "completed",
                                "total_content_length": len(chapter_content_text),
                                "working_flag": False
                            }
                        }
                        
                except Exception as fallback_error:
                    return {
                        "status": "error",
                        "message": f"음악 추천 폴백 처리 중 오류: {str(fallback_error)}"
                    }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"챕터 완료 및 음악 추천 처리 중 오류가 발생했습니다: {str(e)}"
            }

# 전역 소설 처리 인스턴스
novel_processor = NovelProcessor()

def handle_story_continue(user_id: str, user_message: str, book_id: str) -> Dict:
    """
    소설 계속 쓰기 요청 처리 함수
    
    외부 서버에서 호출할 수 있는 함수입니다.
    /story/continue 엔드포인트의 요청을 처리합니다.
    
    매개변수:
        user_id: 사용자 ID
        user_message: 사용자 메시지
        book_id: 책 ID
        
    반환값:
        처리 결과 딕셔너리
    """
    try:
        result = novel_processor.generate_chapter(
            user_id=user_id,
            user_message=user_message,
            book_id=book_id
        )
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"서버 오류: {str(e)}"
        }

def handle_chapter_summary_with_music(user_id: str, book_id: str) -> Dict:
    """
    챕터 요약 및 음악 추천 요청 처리 함수
    
    외부 서버에서 호출할 수 있는 함수입니다.
    /story/chapter/summary_with_music 엔드포인트의 요청을 처리합니다.
    현재 작업 중인 챕터(workingFlag=True)를 찾아 요약을 생성하고 음악을 추천합니다.
    
    매개변수:
        user_id: 사용자 ID
        book_id: 책 ID
        
    반환값:
        처리 결과 딕셔너리
    """
    try:
        result = novel_processor.finish_chapter_and_recommend_music(
            user_id=user_id,
            book_id=book_id
        )
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"서버 오류: {str(e)}"
        }

def get_health_status() -> Dict:
    """
    서버 상태 확인 함수
    
    시스템의 건강 상태를 확인합니다.
    
    반환값:
        상태 정보 딕셔너리
    """
    try:
        # 간단한 DB 연결 테스트
        novel_processor.db_manager.client.admin.command('ping')
        
        return {
            "status": "healthy",
            "message": "소설 생성 서비스가 정상 작동 중입니다",
            "services": {
                "database": "connected",
                "gpt_client": "initialized",
                "emotion_analyzer": "loaded"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"서비스 오류: {str(e)}",
            "services": {
                "database": "error",
                "error_details": str(e)
            }
        }

def get_service_info() -> Dict:
    """
    서비스 정보 반환 함수
    
    API 서비스에 대한 기본 정보를 반환합니다.
    
    반환값:
        서비스 정보 딕셔너리
    """
    return {
        "service": "AI 기반 소설 생성 및 음악 추천 API",
        "version": "1.0.0",
        "description": "사용자의 입력을 받아 AI가 소설을 생성하고 감정에 맞는 음악을 추천하는 서비스",
        "features": [
            "GPT-4 기반 소설 생성",
            "채팅 히스토리 기반 맥락 유지",
            "KoELECTRA 기반 감정 분석",
            "감정 기반 음악 추천"
        ],
        "endpoints": {
            "소설_계속_쓰기": "handle_story_continue()",
            "챕터_요약_음악_추천": "handle_chapter_summary_with_music()",
            "상태_확인": "get_health_status()",
            "서비스_정보": "get_service_info()"
        }
    } 