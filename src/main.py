from typing import Dict, List, Optional
from .api.gpt_client import GPTClient
from .api.rag_client import RAGClient
from .models.novel import Novel
from .models.chapter import Chapter
from .database.db_manager import DatabaseManager
from .utils.prompt_templates import PromptTemplates
from .utils.text_processor import TextProcessor
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class NovelGenerator:
    def __init__(self):
        self.gpt_client = GPTClient()
        self.rag_client = RAGClient()
        self.db_manager = DatabaseManager()
        self.text_processor = TextProcessor()
        self.current_novel: Optional[Novel] = None
        self.chat_history: List[Dict] = []

    async def start_novel_generation(self, genre: str, title: str):
        """
        Start a new novel generation process
        """
        # Search for genre requirements
        genre_requirements = await self.rag_client.search_genre_requirements(genre)
        
        # Create new novel
        self.current_novel = Novel(title=title, genre=genre)
        
        # Generate initial prompt
        prompt = PromptTemplates.get_genre_prompt(genre, genre_requirements)
        
        # Start chat session
        self.chat_history = [
            {"role": "system", "content": "You are a creative novelist."},
            {"role": "user", "content": prompt}
        ]
        
        # Save novel to database
        novel_id = await self.db_manager.save_novel(self.current_novel.to_dict())
        self.current_novel.update_metadata("db_id", novel_id)
        
        return novel_id

    async def generate_chapter(self, chapter_number: int, chapter_title: str):
        """
        Generate a new chapter
        """
        if not self.current_novel:
            raise ValueError("No active novel")

        # Create new chapter
        chapter = Chapter(number=chapter_number, title=chapter_title)
        
        # Get context from previous chapters
        context = {
            "previous_chapters": "\n".join([
                ch.get_content() for ch in self.current_novel.get_all_chapters()
            ]),
            "chapter_outline": f"Chapter {chapter_number}: {chapter_title}"
        }
        
        # Generate chapter prompt
        prompt = PromptTemplates.get_chapter_prompt(chapter_number, context)
        
        # Add to chat history
        self.chat_history.append({"role": "user", "content": prompt})
        
        # Generate content
        content = await self.gpt_client.chat_session(self.chat_history)
        chapter.add_content(content)
        
        # Add response to chat history
        self.chat_history.append({"role": "assistant", "content": content})
        
        # Save chapter to database
        chapter_id = await self.db_manager.save_chapter(
            self.current_novel.metadata["db_id"],
            chapter.to_dict()
        )
        chapter.update_metadata("db_id", chapter_id)
        
        # Add chapter to novel
        self.current_novel.add_chapter(chapter)
        
        return chapter

    async def end_chapter(self, chapter_number: int):
        """
        End current chapter and generate summary
        """
        if not self.current_novel:
            raise ValueError("No active novel")

        chapter = self.current_novel.get_chapter(chapter_number)
        content = chapter.get_content()
        
        # Generate summary
        summary_prompt = PromptTemplates.get_summary_prompt(content)
        summary = await self.gpt_client.summarize_chapter(summary_prompt)
        chapter.set_summary(summary)
        
        # Update chapter in database
        await self.db_manager.save_chapter(
            self.current_novel.metadata["db_id"],
            chapter.to_dict()
        )
        
        # Analyze text metrics
        metrics = self.text_processor.analyze_text_metrics(content)
        chapter.update_metadata("metrics", metrics)
        
        return summary

    async def save_progress(self):
        """
        Save current progress
        """
        if not self.current_novel:
            raise ValueError("No active novel")

        # Update novel in database
        await self.db_manager.save_novel(self.current_novel.to_dict())
        
        # Save chat history
        self.current_novel.update_metadata("chat_history", self.chat_history)
        
        return True

async def main():
    # Example usage
    generator = NovelGenerator()
    
    # Start new novel
    novel_id = await generator.start_novel_generation(
        genre="Fantasy",
        title="The Lost Kingdom"
    )
    
    # Generate first chapter
    chapter = await generator.generate_chapter(
        chapter_number=1,
        chapter_title="The Beginning"
    )
    
    # End chapter and get summary
    summary = await generator.end_chapter(chapter_number=1)
    
    # Save progress
    await generator.save_progress()

if __name__ == "__main__":
    asyncio.run(main()) 