# corsi_engine.py
from datetime import datetime
from typing import List, Dict
import random

from database_manager import DatabaseManager


class CorsiEngine:
    """Logic-only Corsi engine for web backend."""

    MIN_SPAN = 2
    MAX_SPAN = 8
    TRIALS_PER_SPAN = 2
    NUM_BLOCKS = 9  # 3x3 logical blocks

    def __init__(self, candidate_info: Dict):
        self.db = DatabaseManager()
        self.candidate_info = candidate_info
        self.results: List[Dict] = []

        self.current_span = self.MIN_SPAN
        self.current_trial = 1
        self.finished = False

    def start_session(self) -> Dict:
        """
        Called when a new online session begins.
        NOTE: we do NOT save to the database yet.
        Candidate + session are only saved when the task finishes.
        """
        return self._state()

    def _state(self) -> Dict:
        return {
            "span_length": self.current_span,
            "trial_number": self.current_trial,
            "finished": self.finished,
        }

    def new_sequence(self) -> List[int]:
        """Generate a random sequence for the current span length."""
        return random.sample(range(self.NUM_BLOCKS), self.current_span)

    def submit_trial(self, sequence: List[int], response: List[int]) -> Dict:
        """Record one trial and update progression rules."""
        correct = sequence == response
        self.results.append(
            {
                "span_length": self.current_span,
                "trial_number": self.current_trial,
                "sequence": sequence,
                "response": response,
                "correct": correct,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        span_trials = [
            r for r in self.results if r["span_length"] == self.current_span
        ]

        if len(span_trials) >= self.TRIALS_PER_SPAN:
            # Discontinue rule: both trials at this span failed
            if sum(r["correct"] for r in span_trials) == 0:
                self.finished = True
            else:
                if self.current_span < self.MAX_SPAN:
                    self.current_span += 1
                else:
                    self.finished = True
            self.current_trial = 1
        else:
            self.current_trial += 1

        return {
            "correct": correct,
            "finished": self.finished,
            "next_state": self._state(),
        }

    def calculate_corsi_span(self) -> int:
        """Highest span with >= 50% accuracy."""
        spans = {r["span_length"] for r in self.results}
        span_scores = {}
        for span in spans:
            trials = [r for r in self.results if r["span_length"] == span]
            accuracy = sum(t["correct"] for t in trials) / len(trials)
            if accuracy >= 0.5:
                span_scores[span] = accuracy
        return max(span_scores.keys()) if span_scores else 0

    def save_session(self) -> Dict:
        """
        Compute summary and save candidate + session to DB.
        This is only called when the task is finished.
        """
        if not self.results:
            return {}

        total_trials = len(self.results)
        correct_trials = sum(r["correct"] for r in self.results)
        accuracy = (correct_trials / total_trials) * 100
        corsi_span = self.calculate_corsi_span()

        session_data = {
            "session_number": int(self.candidate_info.get("session", 1)),
            "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "corsi_span": corsi_span,
            "total_trials": total_trials,
            "correct_trials": correct_trials,
            "accuracy": accuracy,
            "data_files": [],
        }

        # Only now we persist to database
        self.db.save_candidate(self.candidate_info)
        self.db.save_test_session(self.candidate_info["candidate_id"], session_data)

        return session_data
