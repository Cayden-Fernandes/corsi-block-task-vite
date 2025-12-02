"""
Candidate data model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Candidate:
    """Candidate information model."""
    candidate_id: str
    candidate_name: str
    age: Optional[str] = None
    gender: Optional[str] = None
    examiner_name: Optional[str] = None
    additional_notes: Optional[str] = None
    session: str = "1"