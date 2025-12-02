"""
Main class for running the Corsi Block Tapping Task.
"""

from psychopy import visual, core, event, gui
import pandas as pd
import numpy as np
import random
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from database.database_manager import DatabaseManager
from task.visual_components import VisualComponents
from task.trial_runner import TrialRunner
from utils.file_handler import FileHandler
from utils.validation import validate_candidate_info
from config import *


class CorsiTask:
    """Main class for running the Corsi Block Tapping Task."""
    
    def __init__(self):
        self.win = None
        self.db_manager = DatabaseManager()
        self.visual_components = None
        self.trial_runner = None
        self.file_handler = FileHandler()
        self.exp_info = {}
        self.results = []
        self.block_positions = []
        self.blocks = []
    
    def initialize_window(self):
        """Initialize PsychoPy window if not already created."""
        if self.win is None:
            self.win = visual.Window(
                size=WINDOW_SIZE,
                color='white',
                units='pix',
                fullscr=False
            )
            self.visual_components = VisualComponents(self.win)
            self.trial_runner = TrialRunner(self.win, self.visual_components)
    
    def collect_candidate_details(self) -> bool:
        """Collect candidate details via GUI dialog."""
        exp_info = {
            'examiner_name': '',
            'candidate_name': '',
            'candidate_id': '',
            'age': '',
            'gender': ['Male', 'Female', 'Other', 'Prefer not to say'],
            'session': '1',
            'additional_notes': ''
        }
        
        dlg = gui.DlgFromDict(
            exp_info,
            title='Candidate Details - Examiner Input',
            order=['examiner_name', 'candidate_name', 'candidate_id', 
                   'age', 'gender', 'session', 'additional_notes']
        )
        
        if dlg.OK and validate_candidate_info(exp_info):
            self.exp_info = exp_info
            self.db_manager.save_candidate(exp_info)
            return True
        return False
    
    def show_message(self, message: str, duration: float = 2, wait_for_key: bool = True):
        """Display a message on screen."""
        if self.win is None:
            self.initialize_window()
        
        self.visual_components.show_message(message, duration, wait_for_key)
    
    def main_menu(self):
        """Display and handle main menu."""
        self.initialize_window()
        
        while True:
            menu_text = self._build_menu_text()
            
            menu = visual.TextStim(
                self.win,
                text=menu_text,
                color='black',
                height=20,
                wrapWidth=800
            )
            menu.draw()
            self.win.flip()
            
            keys = event.waitKeys(keyList=['1', '2', '3', '4', '5', 'escape'])
            
            if '1' in keys:
                if not self.exp_info:
                    self.show_message("Please enter candidate details first.", duration=2)
                else:
                    self.run_corsi_task()
            elif '2' in keys:
                self.edit_candidate_details()
            elif '3' in keys:
                self.view_database_status()
            elif '4' in keys:
                self.show_instructions()
            elif '5' in keys or 'escape' in keys:
                self.cleanup()
                break
    
    def _build_menu_text(self) -> str:
        """Build menu text with current candidate info."""
        candidate_info = ""
        if self.exp_info:
            candidate_info = f"""Current Candidate:
Name: {self.exp_info['candidate_name']}
ID: {self.exp_info['candidate_id']}
Age: {self.exp_info['age']}
Examiner: {self.exp_info['examiner_name']}

"""
        
        return f"""{candidate_info}COGNITIVE ASSESSMENT SUITE
Corsi Block Tapping Task

Options:
1. Start Corsi Task
2. Edit Candidate Details
3. View Database Status
4. View Instructions
5. Exit

Press 1, 2, 3, 4, or 5 to select"""
    
    def edit_candidate_details(self) -> bool:
        """Edit existing candidate details."""
        if not self.exp_info:
            self.show_message("No candidate details found. Please enter details first.", duration=2)
            return False
        
        editable_info = self.exp_info.copy()
        
        dlg = gui.DlgFromDict(
            editable_info,
            title='Edit Candidate Details',
            order=['examiner_name', 'candidate_name', 'candidate_id',
                   'age', 'gender', 'session', 'additional_notes']
        )
        
        if dlg.OK and validate_candidate_info(editable_info):
            self.exp_info = editable_info
            self.db_manager.save_candidate(editable_info)
            self.show_message("Candidate details updated successfully!", duration=1.5)
            return True
        return False
    
    def view_database_status(self):
        """Display database statistics."""
        stats = self.db_manager.get_database_stats()
        
        if not stats:
            self.show_message("Error retrieving database statistics.")
            return
        
        status_text = f"""DATABASE STATUS:

Total Candidates: {stats['candidate_count']}
Total Test Sessions: {stats['session_count']}

Recent Sessions:
"""
        
        for name, session, span, date in stats['recent_sessions']:
            status_text += f"• {name} - Session {session} - Span {span} - {date[:10]}\n"
        
        if not stats['recent_sessions']:
            status_text += "No test sessions recorded yet."
        
        self.show_message(status_text)
    
    def show_instructions(self):
        """Display task instructions."""
        instructions = """CORSI BLOCK TAPPING TASK - INSTRUCTIONS

Task Description:
• This test measures visual-spatial working memory
• Blocks will light up in a sequence
• Candidate must reproduce the sequence by clicking blocks

Examiner Controls:
• During task, press 'R' to replay current sequence
• Press 'Q' to quit to main menu
• Press 'ESC' to exit completely

Test Progression:
• Sequence length increases from 2 to 8 blocks
• Block positions randomize each trial
• Each sequence length has 2 trials
• Test stops after 2 consecutive failures at same span

Click to return to main menu."""
        
        self.show_message(instructions)
    
    def run_corsi_task(self):
        """Run the complete Corsi task."""
        self.initialize_window()
        self.results = []
        
        welcome_text = f"""Corsi Block Tapping Task

Candidate: {self.exp_info['candidate_name']}
Examiner: {self.exp_info['examiner_name']}

Instructions:
• Watch the sequence of highlighted blocks
• Click the blocks in the same order
• Sequences will get longer

Controls:
• Press 'R' to replay sequence
• Press 'Q' to quit to main menu

Click to begin the task."""
        
        self.show_message(welcome_text)
        
        success = self.run_main_test()
        
        if success and self.results:
            self.save_all_data()
            self.show_final_results()
    
    def run_main_test(self) -> bool:
        """Execute the main test with increasing sequence lengths."""
        for span_length in range(MIN_SPAN, MAX_SPAN + 1):
            span_results = []
            
            for trial_num in range(TRIALS_PER_SPAN):
                # Generate new positions and sequence
                self.block_positions = self.generate_random_block_positions()
                self.blocks = self.visual_components.create_blocks(self.block_positions)
                sequence = random.sample(range(len(self.blocks)), span_length)
                
                # Run trial
                trial_success = self.trial_runner.run_single_trial(
                    span_length, 
                    trial_num + 1, 
                    sequence,
                    self.blocks,
                    self.exp_info,
                    self.results
                )
                
                if not trial_success:
                    return False  # User quit
                
                span_results.append(self.results[-1]['correct'])
            
            # Check discontinue rule (both trials failed)
            if sum(span_results) == 0:
                break
        
        return True
    
    def generate_random_block_positions(self) -> List[Tuple[int, int]]:
        """Generate random, non-overlapping block positions."""
        positions = []
        x_range = [-350, -200, -50, 50, 200, 350]
        y_range = [-250, -100, 50, 100, 250]
        
        max_attempts = 1000
        attempts = 0
        
        while len(positions) < NUM_BLOCKS and attempts < max_attempts:
            x = random.choice(x_range)
            y = random.choice(y_range)
            pos = (x, y)
            
            # Check distance from all existing positions
            if all(np.sqrt((x - ex)**2 + (y - ey)**2) >= MIN_BLOCK_DISTANCE 
                   for ex, ey in positions):
                positions.append(pos)
            
            attempts += 1
        
        return positions
    
    def calculate_corsi_span(self) -> int:
        """Calculate Corsi span (highest span with ≥50% accuracy)."""
        span_scores = {}
        
        for span in set(r['span_length'] for r in self.results):
            span_trials = [r for r in self.results if r['span_length'] == span]
            accuracy = sum(t['correct'] for t in span_trials) / len(span_trials)
            
            if accuracy >= 0.5:
                span_scores[span] = accuracy
        
        return max(span_scores.keys()) if span_scores else 0
    
    def save_all_data(self) -> List[str]:
        """Save all test data to file and database."""
        if not self.results:
            return []
        
        # Calculate metrics
        total_trials = len(self.results)
        correct_trials = sum(r['correct'] for r in self.results)
        accuracy = (correct_trials / total_trials) * 100
        corsi_span = self.calculate_corsi_span()
        
        # Save to file and database
        saved_files = self.file_handler.save_results(
            self.exp_info,
            self.results,
            corsi_span,
            total_trials,
            correct_trials,
            accuracy
        )
        
        # Save to database
        session_data = {
            'session_number': int(self.exp_info['session']),
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'corsi_span': corsi_span,
            'total_trials': total_trials,
            'correct_trials': correct_trials,
            'accuracy': accuracy,
            'data_files': saved_files
        }
        
        self.db_manager.save_test_session(self.exp_info['candidate_id'], session_data)
        
        return saved_files
    
    def show_final_results(self):
        """Display final test results."""
        total_trials = len(self.results)
        correct_trials = sum(r['correct'] for r in self.results)
        accuracy = (correct_trials / total_trials) * 100
        corsi_span = self.calculate_corsi_span()
        
        results_text = f"""TEST COMPLETE!

Candidate: {self.exp_info['candidate_name']}

Performance Summary:
• Corsi Span Score: {corsi_span}
• Total Trials: {total_trials}
• Correct Responses: {correct_trials}
• Accuracy: {accuracy:.1f}%

Data has been saved successfully.

Press any key to return to main menu."""
        
        self.show_message(results_text)
    
    def cleanup(self):
        """Clean up resources."""
        if self.win:
            self.win.close()
            self.win = None