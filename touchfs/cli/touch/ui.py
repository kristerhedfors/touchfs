"""UI components for TouchFS touch command."""

import os
import curses
from typing import List, Tuple, Optional, Set
from logging import Logger
from openai import OpenAI

from ...config import templates, model
from ...core.context import build_context
from ...models.filename_suggestions import FilenameSuggestions

def get_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = model.get_openai_key()
    return OpenAI(api_key=api_key)

def generate_filename_suggestions(directory: str, selected_filenames: Optional[List[str]] = None, 
                                max_tokens: Optional[int] = None, logger: Optional[Logger] = None) -> List[str]:
    """Generate filename suggestions based on directory context.
    
    Args:
        directory: Directory to analyze for context
        selected_filenames: Optional list of previously selected filenames
        max_tokens: Maximum tokens for context building
        logger: Optional logger for debug output
        
    Returns:
        List of 10 filename suggestions
    """
    try:
        # Build context from directory
        context = build_context(directory, max_tokens=max_tokens)
        
        # Get system prompt template
        system_prompt = templates.read_template(templates.FILENAME_SUGGESTIONS_SYSTEM_PROMPT_TEMPLATE)
        
        # Format prompt with context and selected files
        final_prompt = system_prompt.format(
            context=context,
            selected_files="\n".join(selected_filenames) if selected_filenames else "None"
        )
        
        # Initialize OpenAI client
        client = get_openai_client()
        
        # Get suggestions from OpenAI
        messages = [
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": f"Suggest {10 if not selected_filenames else 10 - len(selected_filenames)} filenames"}
        ]
        
        try:
            completion = client.beta.chat.completions.parse(
                model=model.get_model(),  # Use default model from settings
                messages=messages,
                response_format=FilenameSuggestions,
                temperature=0.7  # Higher temperature for more diverse suggestions
            )
            
            suggestions = completion.choices[0].message.parsed.filenames
            
            # Filter out existing files from OpenAI suggestions
            dir_contents = os.listdir(directory)
            existing_files = {f for f in dir_contents if os.path.isfile(os.path.join(directory, f))}
            suggestions = [s for s in suggestions if s not in existing_files]
            
            # Start with previously selected files if any
            final_suggestions = []
            if selected_filenames:
                final_suggestions.extend(selected_filenames)
            
            # Add new suggestions until we have 10 total
            remaining_slots = 10 - len(final_suggestions)
            if remaining_slots > 0:
                # Add unique suggestions that aren't already selected
                new_suggestions = [s for s in suggestions if s not in final_suggestions]
                final_suggestions.extend(new_suggestions[:remaining_slots])
            
            # If we still need more, add generic ones
            while len(final_suggestions) < 10:
                generic = f"file_{len(final_suggestions)+1}.txt"
                if generic not in final_suggestions and generic not in existing_files:
                    final_suggestions.append(generic)
                
            return final_suggestions[:10]
            
        except Exception as api_error:
            if logger:
                logger.error(f"OpenAI API error: {str(api_error)}")
            raise
            
    except Exception as e:
        if logger:
            logger.error(f"Error generating filename suggestions: {e}")
        return [f"file_{i+1}.txt" for i in range(10)]

def display_menu(suggestions: List[str], allow_multiple: bool = True) -> Tuple[Optional[List[int]], bool]:
    """Display interactive menu for filename selection.
    
    Args:
        suggestions: List of filename suggestions
        allow_multiple: Whether to allow selecting multiple items
        
    Returns:
        Tuple of (selected_indices, regenerate) where:
            selected_indices: List of selected indices, or None if cancelled
            regenerate: True if user requested regeneration of non-selected items
    """
    def setup_curses():
        curses.curs_set(0)  # Hide cursor
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected item
        
    def draw_menu(stdscr, suggestions: List[str], selected: Set[int], current: int):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Draw header
        header = "Select filename(s) - Press SPACE to select, ENTER to confirm, ESC to cancel, r to regenerate"
        if allow_multiple:
            header += " | Multiple selections allowed | Press r to keep selected and regenerate others"
        stdscr.addstr(0, 0, header[:width-1])
        
        # Draw suggestions
        for i, name in enumerate(suggestions):
            if i >= height - 3:  # Leave room for header and footer
                break
                
            style = curses.color_pair(1) if i == current else curses.A_NORMAL
            if i in selected:
                name = f"[*] {name}"
            else:
                name = f"[ ] {name}"
            
            stdscr.addstr(i + 2, 2, name[:width-3], style)
            
        stdscr.refresh()
    
    def menu_loop(stdscr) -> Tuple[Optional[List[int]], bool]:
        setup_curses()
        current = 0
        selected = set()
        
        while True:
            draw_menu(stdscr, suggestions, selected, current)
            key = stdscr.getch()
            
            if key == 27:  # ESC
                return None, False
            elif key == ord('\n'):  # Enter
                if not allow_multiple and not selected:
                    selected.add(current)
                return list(selected) if selected else None, False
            elif key == ord('r'):  # 'r' to regenerate non-selected
                if selected:  # Only allow regeneration if something is selected
                    return list(selected), True
            elif key == ord(' '):  # Space
                if allow_multiple:
                    if current in selected:
                        selected.remove(current)
                    else:
                        selected.add(current)
                else:
                    selected = {current}
            elif key == curses.KEY_UP and current > 0:
                current -= 1
            elif key == curses.KEY_DOWN and current < len(suggestions) - 1:
                current += 1
    
    try:
        return curses.wrapper(menu_loop)
    except Exception:
        return None, False
