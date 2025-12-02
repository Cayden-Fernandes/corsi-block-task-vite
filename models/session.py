"""
Test session data model.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class TrialResult:
    """Individual trial result."""
    span_length: int
    trial_number: int
    sequence: List[int]
    response: List[int]
    correct: bool
    timestamp: datetime


@dataclass
class TestSession:
    """Complete test session data."""
    candidate_id: str
    session_number: int
    test_date: datetime
    corsi_span: int
    total_trials: int
    correct_trials: int
    accuracy: float
    data_files: List[str]
    trial_results: List[TrialResult]