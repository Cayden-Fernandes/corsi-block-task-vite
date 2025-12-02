"""
File handling operations.
"""

import os
import json
from datetime import datetime
from typing import List, Dict


class FileHandler:
    """Handles file operations for saving results."""
    
    def __init__(self, data_folder: str = "corsi_data"):
        self.data_folder = data_folder
        os.makedirs(self.data_folder, exist_ok=True)
    
    def save_results(self, exp_info: Dict, results: List[Dict], 
                    corsi_span: int, total_trials: int, 
                    correct_trials: int, accuracy: float) -> List[str]:
        """Save test results to file."""
        # Save to text file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corsi_results_{exp_info['candidate_id']}_{timestamp}.txt"
        filepath = os.path.join(self.data_folder, filename)
        
        self._write_results_file(filepath, exp_info, results, 
                                corsi_span, total_trials, correct_trials, accuracy)
        
        print(f"✓ Results saved to: {filepath}")
        return [filepath]
    
    def _write_results_file(self, filepath: str, exp_info: Dict, results: List[Dict],
                           corsi_span: int, total_trials: int, 
                           correct_trials: int, accuracy: float):
        """Write detailed results to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("CORSI BLOCK TAPPING TASK - RESULTS\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("CANDIDATE INFORMATION:\n")
            f.write("-" * 30 + "\n")
            for key in ['candidate_name', 'candidate_id', 'age', 'gender', 
                       'examiner_name', 'session']:
                f.write(f"{key.replace('_', ' ').title()}: {exp_info[key]}\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("PERFORMANCE SUMMARY:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Corsi Span Score: {corsi_span}\n")
            f.write(f"Total Trials: {total_trials}\n")
            f.write(f"Correct Trials: {correct_trials}\n")
            f.write(f"Accuracy: {accuracy:.1f}%\n\n")
            
            f.write("DETAILED TRIAL RESULTS:\n")
            f.write("-" * 30 + "\n")
            for result in results:
                status = "PASS" if result['correct'] else "FAIL"
                f.write(f"Span {result['span_length']} - Trial {result['trial_number']}: {status}\n")
                f.write(f"  Sequence: {result['sequence']}\n")
                f.write(f"  Response: {result['response']}\n\n")