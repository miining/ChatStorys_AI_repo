from typing import List, Dict
from datetime import datetime
from .chapter import Chapter

class Novel:
    def __init__(self, title: str, genre: str):
        self.title = title
        self.genre = genre
        self.chapters: List[Chapter] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict = {}

    def add_chapter(self, chapter: Chapter):
        """
        Add a new chapter to the novel
        """
        if not isinstance(chapter, Chapter):
            raise ValueError("Invalid chapter object")
        self.chapters.append(chapter)
        self.updated_at = datetime.now()

    def get_chapter(self, chapter_number: int) -> Chapter:
        """
        Get a specific chapter by number
        """
        for chapter in self.chapters:
            if chapter.number == chapter_number:
                return chapter
        raise ValueError(f"Chapter {chapter_number} not found")

    def get_all_chapters(self) -> List[Chapter]:
        """
        Get all chapters
        """
        return self.chapters

    def update_metadata(self, key: str, value: any):
        """
        Update novel metadata
        """
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """
        Convert novel object to dictionary
        """
        return {
            "title": self.title,
            "genre": self.genre,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Novel':
        """
        Create novel object from dictionary
        """
        novel = cls(data["title"], data["genre"])
        novel.created_at = datetime.fromisoformat(data["created_at"])
        novel.updated_at = datetime.fromisoformat(data["updated_at"])
        novel.metadata = data["metadata"]
        
        for chapter_data in data["chapters"]:
            chapter = Chapter.from_dict(chapter_data)
            novel.add_chapter(chapter)
        
        return novel 