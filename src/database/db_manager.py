'''
We can use external DB
'''

# from typing import Optional
# from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship
# from datetime import datetime
# import os
# from dotenv import load_dotenv

# load_dotenv()

# Base = declarative_base()

# class NovelDB(Base):
#     __tablename__ = 'novels'

#     id = Column(Integer, primary_key=True)
#     title = Column(String, nullable=False)
#     genre = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.now)
#     updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
#     metadata = Column(JSON)
#     chapters = relationship("ChapterDB", back_populates="novel")

# class ChapterDB(Base):
#     __tablename__ = 'chapters'

#     id = Column(Integer, primary_key=True)
#     novel_id = Column(Integer, ForeignKey('novels.id'))
#     number = Column(Integer, nullable=False)
#     title = Column(String, nullable=False)
#     content = Column(JSON)
#     summary = Column(String)
#     created_at = Column(DateTime, default=datetime.now)
#     updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
#     metadata = Column(JSON)
#     novel = relationship("NovelDB", back_populates="chapters")

# class DatabaseManager:
#     def __init__(self, connection_string: str = None):
#         self.connection_string = connection_string or os.getenv("DATABASE_URL")
#         if not self.connection_string:
#             raise ValueError("Database connection string is required")
        
#         self.engine = create_engine(self.connection_string)
#         Base.metadata.create_all(self.engine)
#         self.Session = sessionmaker(bind=self.engine)

#     async def save_novel(self, novel_data: dict):
#         """
#         Save novel data to database
#         """
#         session = self.Session()
#         try:
#             novel = NovelDB(
#                 title=novel_data["title"],
#                 genre=novel_data["genre"],
#                 created_at=datetime.fromisoformat(novel_data["created_at"]),
#                 updated_at=datetime.fromisoformat(novel_data["updated_at"]),
#                 metadata=novel_data["metadata"]
#             )
#             session.add(novel)
#             session.commit()
#             return novel.id
#         except Exception as e:
#             session.rollback()
#             raise Exception(f"Error saving novel: {str(e)}")
#         finally:
#             session.close()

#     async def save_chapter(self, novel_id: int, chapter_data: dict):
#         """
#         Save chapter data to database
#         """
#         session = self.Session()
#         try:
#             chapter = ChapterDB(
#                 novel_id=novel_id,
#                 number=chapter_data["number"],
#                 title=chapter_data["title"],
#                 content=chapter_data["content"],
#                 summary=chapter_data["summary"],
#                 created_at=datetime.fromisoformat(chapter_data["created_at"]),
#                 updated_at=datetime.fromisoformat(chapter_data["updated_at"]),
#                 metadata=chapter_data["metadata"]
#             )
#             session.add(chapter)
#             session.commit()
#             return chapter.id
#         except Exception as e:
#             session.rollback()
#             raise Exception(f"Error saving chapter: {str(e)}")
#         finally:
#             session.close()

#     async def get_novel_by_id(self, novel_id: int) -> Optional[dict]:
#         """
#         Get novel by ID
#         """
#         session = self.Session()
#         try:
#             novel = session.query(NovelDB).filter(NovelDB.id == novel_id).first()
#             if novel:
#                 return {
#                     "id": novel.id,
#                     "title": novel.title,
#                     "genre": novel.genre,
#                     "created_at": novel.created_at.isoformat(),
#                     "updated_at": novel.updated_at.isoformat(),
#                     "metadata": novel.metadata
#                 }
#             return None
#         finally:
#             session.close()

#     async def get_chapter_by_number(self, novel_id: int, chapter_number: int) -> Optional[dict]:
#         """
#         Get chapter by novel ID and chapter number
#         """
#         session = self.Session()
#         try:
#             chapter = session.query(ChapterDB).filter(
#                 ChapterDB.novel_id == novel_id,
#                 ChapterDB.number == chapter_number
#             ).first()
#             if chapter:
#                 return {
#                     "id": chapter.id,
#                     "novel_id": chapter.novel_id,
#                     "number": chapter.number,
#                     "title": chapter.title,
#                     "content": chapter.content,
#                     "summary": chapter.summary,
#                     "created_at": chapter.created_at.isoformat(),
#                     "updated_at": chapter.updated_at.isoformat(),
#                     "metadata": chapter.metadata
#                 }
#             return None
#         finally:
#             session.close() 