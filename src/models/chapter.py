from typing import Dict, List
from datetime import datetime

class Chapter:
    def __init__(self, number: int, title: str):
        self.number = number
        self.title = title
        self.content: List[str] = []
        self.summary: str = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict = {}

    def add_content(self, content: str):
        """
        Add content to the chapter
        """
        self.content.append(content)
        self.updated_at = datetime.now()

    def get_content(self) -> str:
        """
        Get all chapter content
        """
        return "\n".join(self.content)

    def set_summary(self, summary: str):
        """
        Set chapter summary
        """
        self.summary = summary
        self.updated_at = datetime.now()

    def get_summary(self) -> str:
        """
        Get chapter summary
        """
        return self.summary

    def update_metadata(self, key: str, value: any):
        """
        Update chapter metadata
        """
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """
        Convert chapter object to dictionary
        """
        return {
            "number": self.number,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Chapter':
        """
        Create chapter object from dictionary
        """
        chapter = cls(data["number"], data["title"])
        chapter.content = data["content"]
        chapter.summary = data["summary"]
        chapter.created_at = datetime.fromisoformat(data["created_at"])
        chapter.updated_at = datetime.fromisoformat(data["updated_at"])
        chapter.metadata = data["metadata"]
        return chapter 