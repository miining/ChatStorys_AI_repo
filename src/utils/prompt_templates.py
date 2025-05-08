class PromptTemplates:
    @staticmethod
    def get_genre_prompt(genre: str, requirements: dict) -> str:
        """
        Generate prompt for genre-specific novel generation
        """
        return f"""You are a creative novelist specializing in {genre} novels.
Based on the following requirements and guidelines, create an engaging story:

Genre Requirements:
{requirements.get('requirements', '')}

Please create a novel that follows these guidelines while maintaining originality and creativity.
Focus on developing compelling characters and an engaging plot that fits the {genre} genre."""

    @staticmethod
    def get_chapter_prompt(chapter_number: int, context: dict) -> str:
        """
        Generate prompt for chapter generation
        """
        return f"""You are continuing to write chapter {chapter_number} of the novel.
Previous context:
{context.get('previous_chapters', '')}

Current chapter outline:
{context.get('chapter_outline', '')}

Please continue writing the story, maintaining consistency with previous chapters and following the established plot and character development."""

    @staticmethod
    def get_summary_prompt(chapter_content: str) -> str:
        """
        Generate prompt for chapter summarization
        """
        return f"""Please provide a concise summary of the following chapter content:

{chapter_content}

Focus on the main plot points, character development, and significant events.
Keep the summary clear and informative while maintaining the essence of the chapter."""

    @staticmethod
    def get_character_development_prompt(character_name: str, context: dict) -> str:
        """
        Generate prompt for character development
        """
        return f"""Develop the character {character_name} based on the following context:

Previous character development:
{context.get('previous_development', '')}

Current situation:
{context.get('current_situation', '')}

Please provide detailed character development that is consistent with previous appearances and advances the story."""

    @staticmethod
    def get_plot_development_prompt(context: dict) -> str:
        """
        Generate prompt for plot development
        """
        return f"""Based on the following story context, develop the plot:

Previous plot points:
{context.get('previous_plot', '')}

Current situation:
{context.get('current_situation', '')}

Please develop the plot in a way that maintains consistency, creates tension, and advances the story meaningfully.""" 