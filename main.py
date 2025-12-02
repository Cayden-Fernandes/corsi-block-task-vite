"""
Corsi Block Tapping Task - Cognitive Assessment Suite
======================================================
Main entry point for the Corsi Block Tapping Task application.

Author: Cognitive Assessment Team
Version: 2.0
"""

from task.corsi_task import CorsiTask


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