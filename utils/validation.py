"""
Input validation functions.
"""

from typing import Dict


def validate_candidate_info(info: Dict) -> bool:
    """Validate candidate information."""
    if not info['candidate_name'] or not info['candidate_id']:
        return False
    
    try:
        session = int(info['session'])
        if session < 1:
            raise ValueError
    except ValueError:
        return False
    
    return True