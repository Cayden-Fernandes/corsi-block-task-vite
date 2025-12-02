"""
Visual components for the Corsi task.
"""

from psychopy import visual
from typing import List, Tuple
from config import *


class VisualComponents:
    """Handles creation and management of visual stimuli."""
    
    def __init__(self, window):
        self.win = window
    
    def create_blocks(self, positions: List[Tuple[int, int]]):
        """Create visual block stimuli."""
        return [
            visual.Rect(
                self.win,
                width=BLOCK_SIZE,
                height=BLOCK_SIZE,
                fillColor='lightblue',
                lineColor='darkblue',
                pos=pos
            )
            for pos in positions
        ]
    
    def show_message(self, message: str, duration: float = 2, wait_for_key: bool = True):
        """Display a message on screen."""
        text = visual.TextStim(
            self.win,
            text=message,
            color='black',
            height=20,
            wrapWidth=800
        )
        text.draw()
        self.win.flip()
        
        if wait_for_key:
            from psychopy import event
            event.waitKeys()
        else:
            from psychopy import core
            core.wait(duration)
    
    def draw_scene(self, blocks: List[visual.Rect], additional_stims: List = None):
        """Draw all blocks and additional stimuli."""
        for block in blocks:
            block.draw()
        
        if additional_stims:
            for stim in additional_stims:
                stim.draw()
        
        self.win.flip()