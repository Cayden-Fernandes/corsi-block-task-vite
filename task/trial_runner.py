"""
Trial execution logic for the Corsi task.
"""

from psychopy import visual, core, event
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import *


class TrialRunner:
    """Handles execution of individual trials."""
    
    def __init__(self, window, visual_components):
        self.win = window
        self.visual = visual_components
    
    def run_single_trial(self, span_length: int, trial_num: int, sequence: List[int],
                        blocks: List[visual.Rect], exp_info: Dict, results: List) -> bool:
        """Execute a single trial."""
        # Show trial info
        trial_info = visual.TextStim(
            self.win,
            text=f"Trial {trial_num} - Sequence Length: {span_length}\n\nGet ready...",
            color='black',
            height=25,
            pos=(0, 400)
        )
        
        self.visual.draw_scene(blocks, [trial_info])
        core.wait(0.5)
        
        # Display sequence
        if not self._show_sequence(sequence, blocks, trial_info):
            return False
        
        # Get response
        response = self._get_participant_response(span_length, sequence, blocks, trial_info)
        
        if response is None:
            return False
        
        # Record result
        self._record_trial_result(span_length, trial_num, sequence, response, exp_info, results)
        
        # Show feedback
        self._show_feedback(response == sequence)
        
        return True
    
    def _show_sequence(self, sequence: List[int], blocks: List[visual.Rect], 
                      trial_info: visual.TextStim) -> bool:
        """Display the sequence to memorize."""
        for block_idx in sequence:
            if self._check_quit_keys():
                return False
            
            # Highlight block
            blocks[block_idx].fillColor = 'red'
            self.visual.draw_scene(blocks, [trial_info])
            core.wait(0.3)
            
            # Return to normal
            blocks[block_idx].fillColor = 'lightblue'
            self.visual.draw_scene(blocks, [trial_info])
            core.wait(0.3)
        
        return True
    
    def _get_participant_response(self, span_length: int, sequence: List[int], 
                                  blocks: List[visual.Rect], trial_info: visual.TextStim) -> Optional[List[int]]:
        """Collect participant's response."""
        response_sequence = []
        instruction = visual.TextStim(
            self.win,
            text=f"Click the blocks in order\n\nPress 'R' to replay sequence",
            color='black',
            height=25,
            pos=(0, 400)
        )
        
        mouse = event.Mouse()
        
        while len(response_sequence) < span_length:
            if self._check_quit_keys():
                return None
            
            # Check for replay request
            keys = event.getKeys(keyList=['r', 'R'])
            if keys:
                self._replay_sequence(sequence, blocks)
                response_sequence = []
                continue
            
            self.visual.draw_scene(blocks, [instruction])
            
            # Check for mouse click
            if mouse.getPressed()[0]:
                mouse_pos = mouse.getPos()
                
                for i, block in enumerate(blocks):
                    if self._is_click_on_block(mouse_pos, block.pos):
                        if i not in response_sequence:
                            response_sequence.append(i)
                            self._flash_block(i, blocks, 'orange')
                        break
                
                core.wait(0.3)  # Debounce
                event.clearEvents()
        
        return response_sequence
    
    def _replay_sequence(self, sequence: List[int], blocks: List[visual.Rect]):
        """Replay the sequence for the participant."""
        self.visual.show_message("Replaying sequence...", duration=1, wait_for_key=False)
        
        for block_idx in sequence:
            blocks[block_idx].fillColor = 'yellow'
            self.visual.draw_scene(blocks)
            core.wait(0.3)
            
            blocks[block_idx].fillColor = 'lightblue'
            self.visual.draw_scene(blocks)
            core.wait(0.3)
    
    def _flash_block(self, block_idx: int, blocks: List[visual.Rect], color: str):
        """Flash a block with specified color."""
        original_color = blocks[block_idx].fillColor
        blocks[block_idx].fillColor = color
        self.visual.draw_scene(blocks)
        core.wait(0.2)
        blocks[block_idx].fillColor = original_color
    
    def _is_click_on_block(self, mouse_pos: Tuple[float, float], 
                           block_pos: Tuple[int, int]) -> bool:
        """Check if mouse click is within a block."""
        half_size = BLOCK_SIZE / 2
        return (abs(mouse_pos[0] - block_pos[0]) < half_size and
                abs(mouse_pos[1] - block_pos[1]) < half_size)
    
    def _check_quit_keys(self) -> bool:
        """Check for quit keys and handle accordingly."""
        keys = event.getKeys(keyList=['q', 'Q', 'escape'])
        
        if 'escape' in keys:
            # Clean exit
            from task.corsi_task import CorsiTask
            task = CorsiTask()
            task.cleanup()
            exit()
        elif 'q' in keys or 'Q' in keys:
            self.visual.show_message("Returning to main menu...", duration=1, wait_for_key=False)
            return True
        
        return False
    
    def _record_trial_result(self, span_length: int, trial_num: int,
                            sequence: List[int], response: List[int],
                            exp_info: Dict, results: List):
        """Record trial results."""
        result = {
            'candidate_name': exp_info['candidate_name'],
            'candidate_id': exp_info['candidate_id'],
            'age': exp_info['age'],
            'gender': exp_info['gender'],
            'examiner_name': exp_info['examiner_name'],
            'span_length': span_length,
            'trial_number': trial_num,
            'sequence': '-'.join(map(str, sequence)),
            'response': '-'.join(map(str, response)),
            'correct': response == sequence,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        results.append(result)
    
    def _show_feedback(self, correct: bool):
        """Display feedback for trial result."""
        feedback_text = "✓ Correct!" if correct else "✗ Incorrect"
        feedback_color = 'green' if correct else 'red'
        
        feedback = visual.TextStim(
            self.win,
            text=feedback_text,
            color=feedback_color,
            height=30
        )
        feedback.draw()
        self.win.flip()
        core.wait(1.5)