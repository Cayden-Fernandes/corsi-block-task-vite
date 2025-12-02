"""
Corsi Block Tapping Task - Cognitive Assessment Suite
======================================================
A professional implementation of the Corsi Block Tapping Task for assessing
visual-spatial working memory with integrated candidate management and database storage.

Author: Cognitive Assessment Team
Version: 2.0
"""

from psychopy import visual, core, event, gui
import pandas as pd
import numpy as np
import random
import os
import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Tuple, Optional


class DatabaseManager:
    """Handles all database operations for candidate and session management."""
    
    def __init__(self, db_file: str = "candidates_database.db"):
        self.db_file = db_file
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        finally:
            conn.close()
    
    def initialize_database(self):
        """Initialize SQLite database with proper schema and indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create candidates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id TEXT PRIMARY KEY,
                    candidate_name TEXT NOT NULL,
                    age TEXT,
                    gender TEXT,
                    examiner_name TEXT,
                    additional_notes TEXT,
                    date_created TEXT NOT NULL,
                    total_sessions INTEGER DEFAULT 0,
                    last_session_date TEXT
                )
            ''')
            
            # Create test_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT NOT NULL,
                    session_number INTEGER NOT NULL,
                    test_date TEXT NOT NULL,
                    corsi_span INTEGER,
                    total_trials INTEGER,
                    correct_trials INTEGER,
                    accuracy REAL,
                    data_files TEXT,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_candidate 
                ON test_sessions(candidate_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_date 
                ON test_sessions(test_date)
            ''')
            
            conn.commit()
        
        print("✓ Database initialized successfully")
    
    def save_candidate(self, candidate_info: Dict) -> bool:
        """Save or update candidate information."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Check if candidate exists
                cursor.execute(
                    'SELECT total_sessions FROM candidates WHERE candidate_id = ?',
                    (candidate_info['candidate_id'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing candidate
                    cursor.execute('''
                        UPDATE candidates 
                        SET candidate_name = ?, age = ?, gender = ?, 
                            examiner_name = ?, additional_notes = ?,
                            last_session_date = ?
                        WHERE candidate_id = ?
                    ''', (
                        candidate_info['candidate_name'],
                        candidate_info['age'],
                        candidate_info['gender'],
                        candidate_info['examiner_name'],
                        candidate_info['additional_notes'],
                        current_time,
                        candidate_info['candidate_id']
                    ))
                else:
                    # Insert new candidate
                    cursor.execute('''
                        INSERT INTO candidates 
                        (candidate_id, candidate_name, age, gender, examiner_name, 
                         additional_notes, date_created, total_sessions, last_session_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ''', (
                        candidate_info['candidate_id'],
                        candidate_info['candidate_name'],
                        candidate_info['age'],
                        candidate_info['gender'],
                        candidate_info['examiner_name'],
                        candidate_info['additional_notes'],
                        current_time,
                        current_time
                    ))
                
                conn.commit()
            return True
        except Exception as e:
            print(f"✗ Error saving candidate: {e}")
            return False
    
    def save_test_session(self, candidate_id: str, session_data: Dict) -> bool:
        """Save test session results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Increment session count
                cursor.execute('''
                    UPDATE candidates 
                    SET total_sessions = total_sessions + 1,
                        last_session_date = ?
                    WHERE candidate_id = ?
                ''', (session_data['test_date'], candidate_id))
                
                # Insert session record
                cursor.execute('''
                    INSERT INTO test_sessions 
                    (candidate_id, session_number, test_date, corsi_span, 
                     total_trials, correct_trials, accuracy, data_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate_id,
                    session_data['session_number'],
                    session_data['test_date'],
                    session_data['corsi_span'],
                    session_data['total_trials'],
                    session_data['correct_trials'],
                    session_data['accuracy'],
                    json.dumps(session_data['data_files'])
                ))
                
                conn.commit()
            return True
        except Exception as e:
            print(f"✗ Error saving test session: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM candidates")
                candidate_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM test_sessions")
                session_count = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT c.candidate_name, t.session_number, t.corsi_span, t.test_date 
                    FROM test_sessions t 
                    JOIN candidates c ON t.candidate_id = c.candidate_id 
                    ORDER BY t.test_date DESC 
                    LIMIT 5
                ''')
                recent_sessions = cursor.fetchall()
                
                return {
                    'candidate_count': candidate_count,
                    'session_count': session_count,
                    'recent_sessions': recent_sessions
                }
        except Exception as e:
            print(f"✗ Database error: {e}")
            return None


class CorsiTask:
    """Main class for running the Corsi Block Tapping Task."""
    
    # Class constants
    WINDOW_SIZE = (1000, 800)
    BLOCK_SIZE = 80
    MIN_BLOCK_DISTANCE = 120
    NUM_BLOCKS = 9
    MIN_SPAN = 2
    MAX_SPAN = 8
    TRIALS_PER_SPAN = 2
    
    def __init__(self):
        self.win = None
        self.db_manager = DatabaseManager()
        self.exp_info = {}
        self.results = []
        self.block_positions = []
        self.blocks = []
        self.data_folder = "corsi_data"
        
        # Create data folder
        os.makedirs(self.data_folder, exist_ok=True)
    
    def initialize_window(self):
        """Initialize PsychoPy window if not already created."""
        if self.win is None:
            self.win = visual.Window(
                size=self.WINDOW_SIZE,
                color='white',
                units='pix',
                fullscr=False
            )
    
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
        
        if dlg.OK and self._validate_candidate_info(exp_info):
            self.exp_info = exp_info
            self.db_manager.save_candidate(exp_info)
            return True
        return False
    
    def _validate_candidate_info(self, info: Dict) -> bool:
        """Validate candidate information."""
        if not info['candidate_name'] or not info['candidate_id']:
            self.show_message("Candidate name and ID are required!", duration=2)
            return False
        
        try:
            session = int(info['session'])
            if session < 1:
                raise ValueError
        except ValueError:
            self.show_message("Session number must be a positive integer!", duration=2)
            return False
        
        return True
    
    def show_message(self, message: str, duration: float = 2, wait_for_key: bool = True):
        """Display a message on screen."""
        if self.win is None:
            self.initialize_window()
        
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
            event.waitKeys()
        else:
            core.wait(duration)
    
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
        
        if dlg.OK and self._validate_candidate_info(editable_info):
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
    
    def generate_random_block_positions(self) -> List[Tuple[int, int]]:
        """Generate random, non-overlapping block positions."""
        positions = []
        x_range = [-350, -200, -50, 50, 200, 350]
        y_range = [-250, -100, 50, 100, 250]
        
        max_attempts = 1000
        attempts = 0
        
        while len(positions) < self.NUM_BLOCKS and attempts < max_attempts:
            x = random.choice(x_range)
            y = random.choice(y_range)
            pos = (x, y)
            
            # Check distance from all existing positions
            if all(np.sqrt((x - ex)**2 + (y - ey)**2) >= self.MIN_BLOCK_DISTANCE 
                   for ex, ey in positions):
                positions.append(pos)
            
            attempts += 1
        
        return positions
    
    def create_blocks(self):
        """Create visual block stimuli."""
        self.blocks = [
            visual.Rect(
                self.win,
                width=self.BLOCK_SIZE,
                height=self.BLOCK_SIZE,
                fillColor='lightblue',
                lineColor='darkblue',
                pos=pos
            )
            for pos in self.block_positions
        ]
    
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
        for span_length in range(self.MIN_SPAN, self.MAX_SPAN + 1):
            span_results = []
            
            for trial_num in range(self.TRIALS_PER_SPAN):
                # Generate new positions and sequence
                self.block_positions = self.generate_random_block_positions()
                self.create_blocks()
                sequence = random.sample(range(len(self.blocks)), span_length)
                
                # Run trial
                trial_success = self.run_single_trial(span_length, trial_num + 1, sequence)
                
                if not trial_success:
                    return False  # User quit
                
                span_results.append(self.results[-1]['correct'])
            
            # Check discontinue rule (both trials failed)
            if sum(span_results) == 0:
                break
        
        return True
    
    def run_single_trial(self, span_length: int, trial_num: int, sequence: List[int]) -> bool:
        """Execute a single trial."""
        # Show trial info
        trial_info = visual.TextStim(
            self.win,
            text=f"Trial {trial_num} - Sequence Length: {span_length}\n\nGet ready...",
            color='black',
            height=25,
            pos=(0, 400)
        )
        
        self._draw_scene([trial_info])
        core.wait(0.5)
        
        # Display sequence
        if not self._show_sequence(sequence, trial_info):
            return False
        
        # Get response
        response = self._get_participant_response(span_length, sequence, trial_info)
        
        if response is None:
            return False
        
        # Record result
        self._record_trial_result(span_length, trial_num, sequence, response)
        
        # Show feedback
        self._show_feedback(response == sequence)
        
        return True
    
    def _show_sequence(self, sequence: List[int], trial_info: visual.TextStim) -> bool:
        """Display the sequence to memorize."""
        for block_idx in sequence:
            if self._check_quit_keys():
                return False
            
            # Highlight block
            self.blocks[block_idx].fillColor = 'red'
            self._draw_scene([trial_info])
            core.wait(0.3)
            
            # Return to normal
            self.blocks[block_idx].fillColor = 'lightblue'
            self._draw_scene([trial_info])
            core.wait(0.3)
        
        return True
    
    def _get_participant_response(self, span_length: int, sequence: List[int], 
                                   trial_info: visual.TextStim) -> Optional[List[int]]:
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
                self._replay_sequence(sequence)
                response_sequence = []
                continue
            
            self._draw_scene([instruction])
            
            # Check for mouse click
            if mouse.getPressed()[0]:
                mouse_pos = mouse.getPos()
                
                for i, pos in enumerate(self.block_positions):
                    if self._is_click_on_block(mouse_pos, pos):
                        if i not in response_sequence:
                            response_sequence.append(i)
                            self._flash_block(i, 'orange')
                        break
                
                core.wait(0.3)  # Debounce
                event.clearEvents()
        
        return response_sequence
    
    def _replay_sequence(self, sequence: List[int]):
        """Replay the sequence for the participant."""
        self.show_message("Replaying sequence...", duration=1, wait_for_key=False)
        
        for block_idx in sequence:
            self.blocks[block_idx].fillColor = 'yellow'
            self._draw_scene()
            core.wait(0.3)
            
            self.blocks[block_idx].fillColor = 'lightblue'
            self._draw_scene()
            core.wait(0.3)
    
    def _flash_block(self, block_idx: int, color: str):
        """Flash a block with specified color."""
        original_color = self.blocks[block_idx].fillColor
        self.blocks[block_idx].fillColor = color
        self._draw_scene()
        core.wait(0.2)
        self.blocks[block_idx].fillColor = original_color
    
    def _draw_scene(self, additional_stims: List = None):
        """Draw all blocks and additional stimuli."""
        for block in self.blocks:
            block.draw()
        
        if additional_stims:
            for stim in additional_stims:
                stim.draw()
        
        self.win.flip()
    
    def _is_click_on_block(self, mouse_pos: Tuple[float, float], 
                           block_pos: Tuple[int, int]) -> bool:
        """Check if mouse click is within a block."""
        half_size = self.BLOCK_SIZE / 2
        return (abs(mouse_pos[0] - block_pos[0]) < half_size and
                abs(mouse_pos[1] - block_pos[1]) < half_size)
    
    def _check_quit_keys(self) -> bool:
        """Check for quit keys and handle accordingly."""
        keys = event.getKeys(keyList=['q', 'Q', 'escape'])
        
        if 'escape' in keys:
            self.cleanup()
            exit()
        elif 'q' in keys or 'Q' in keys:
            self.show_message("Returning to main menu...", duration=1, wait_for_key=False)
            return True
        
        return False
    
    def _record_trial_result(self, span_length: int, trial_num: int,
                            sequence: List[int], response: List[int]):
        """Record trial results."""
        result = {
            'candidate_name': self.exp_info['candidate_name'],
            'candidate_id': self.exp_info['candidate_id'],
            'age': self.exp_info['age'],
            'gender': self.exp_info['gender'],
            'examiner_name': self.exp_info['examiner_name'],
            'span_length': span_length,
            'trial_number': trial_num,
            'sequence': '-'.join(map(str, sequence)),
            'response': '-'.join(map(str, response)),
            'correct': response == sequence,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.results.append(result)
    
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
        
        # Save to text file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corsi_results_{self.exp_info['candidate_id']}_{timestamp}.txt"
        filepath = os.path.join(self.data_folder, filename)
        
        self._write_results_file(filepath, corsi_span, total_trials, correct_trials, accuracy)
        
        # Save to database
        session_data = {
            'session_number': int(self.exp_info['session']),
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'corsi_span': corsi_span,
            'total_trials': total_trials,
            'correct_trials': correct_trials,
            'accuracy': accuracy,
            'data_files': [filepath]
        }
        
        self.db_manager.save_test_session(self.exp_info['candidate_id'], session_data)
        
        print(f"✓ Results saved to: {filepath}")
        return [filepath]
    
    def _write_results_file(self, filepath: str, corsi_span: int, 
                           total_trials: int, correct_trials: int, accuracy: float):
        """Write detailed results to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("CORSI BLOCK TAPPING TASK - RESULTS\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("CANDIDATE INFORMATION:\n")
            f.write("-" * 30 + "\n")
            for key in ['candidate_name', 'candidate_id', 'age', 'gender', 
                       'examiner_name', 'session']:
                f.write(f"{key.replace('_', ' ').title()}: {self.exp_info[key]}\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("PERFORMANCE SUMMARY:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Corsi Span Score: {corsi_span}\n")
            f.write(f"Total Trials: {total_trials}\n")
            f.write(f"Correct Trials: {correct_trials}\n")
            f.write(f"Accuracy: {accuracy:.1f}%\n\n")
            
            f.write("DETAILED TRIAL RESULTS:\n")
            f.write("-" * 30 + "\n")
            for result in self.results:
                status = "PASS" if result['correct'] else "FAIL"
                f.write(f"Span {result['span_length']} - Trial {result['trial_number']}: {status}\n")
                f.write(f"  Sequence: {result['sequence']}\n")
                f.write(f"  Response: {result['response']}\n\n")
    
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


def main():
    """Main entry point for the Corsi task application."""
    print("\n" + "=" * 60)
    print("  COGNITIVE ASSESSMENT SUITE - Corsi Block Tapping Task")
    print("=" * 60 + "\n")
    
    task = CorsiTask()
    
    try:
        if task.collect_candidate_details():
            task.main_menu()
        else:
            print("Application cancelled.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        task.cleanup()
        print("\nThank you for using the Cognitive Assessment Suite!")


if __name__ == "__main__":
    main()