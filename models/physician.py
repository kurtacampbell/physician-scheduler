"""Physician Module

This module defines the Physician class which represents a physician in the scheduling system.
Physicians have attributes like name, blocked dates, assigned dates, and carryover dates from
previous schedules. The class provides methods to check availability and manage assignments.
"""

from datetime import date, datetime, timedelta

class Physician:
    """A class representing a physician in the scheduling system.

    This class manages physician scheduling data including blocked dates, assignments,
    and carryover dates from previous schedules. It provides methods to check 
    availability and manage assignments.

    Attributes:
        name (str): The physician's name
        blocked_dates (dict): Dictionary mapping dates to blocked assignment types
        assigned_dates (list): List of DateAssignment objects assigned to this physician
        carryover_dates (dict): Dictionary tracking excess assignments from previous schedule
    """
    def __init__(self, name, blocked_dates=None):
        """Initialize a Physician object."""
        self.name = name

        # Initialize blocked_dates as a new dictionary for each instance
        self.blocked_dates = {} if blocked_dates is None else blocked_dates

        # self.assigned_dates: List of DateAssignment objects
        self.assigned_dates = []  # List of DateAssignment objects

        # self.carryover_dates: Dict tracking excess assignments from previous schedule
        # e.g. {"Night": 1} means one extra night shift was assigned last time
        self.carryover_dates = {}

    def is_available(self, check_date: date, assignment_type: str = None) -> bool:
        """Check if the physician is available on a given date for a specific assignment type.
        
        Args:
            check_date (date): The date to check availability for
            assignment_type (str, optional): The type of assignment to check. 
            If None, checks for any block.
        
        Returns:
            bool: True if the physician is available, False otherwise
        """
        if check_date not in self.blocked_dates:
            return True

        if assignment_type is None:
            return False

        blocked_types = self.blocked_dates[check_date]
        return not (blocked_types == [] or assignment_type in blocked_types)

    def assign_date(self, date_assignment):
        """Assign a date to the physician.
        
        Args:
            date_assignment (DateAssignment): The date to assign
        """
        self.assigned_dates.append(date_assignment)

    def add_blocked_dates(self, blocked_dates):
        """Add blocked dates to the physician.
        
        Args:
            blocked_dates (list): List of dictionaries, where each dictionary contains:
                - 'start': Required start date of blocked period (str in YYYY-MM-DD format)
                - 'end': Required end date of blocked period (str in YYYY-MM-DD format)
                - 'name': Optional description of the blocked period (str)
                - 'type': Optional list of specific assignment types that are blocked
        """
        for blocked_range in blocked_dates:
            start = datetime.strptime(blocked_range['start'], '%Y-%m-%d').date()
            end = datetime.strptime(blocked_range['end'], '%Y-%m-%d').date()
            types = blocked_range.get('type', [])  # Get types, default to empty list if not present

            # Add all dates in range
            current = start
            while current <= end:
                if current not in self.blocked_dates:
                    self.blocked_dates[current] = []
                # Add types to the list for this date
                self.blocked_dates[current].extend(types)
                current += timedelta(days=1)

    def get_last_assignment_date(self, assignment_type):
        """Returns the date of the physician's most recent assignment.
        
        Returns:
            datetime.date: The date of the last assignment
            None: If the physician has no assignments of the specified type
        """
        matching_assignments = [assignment.date for assignment in self.assigned_dates 
                              if assignment.type == assignment_type]
        return max(matching_assignments) if matching_assignments else None

    def get_days_since_last_assignment(self, dates, current_date, assignment_type):
        """Get the number of days since the physician's last assignment of the specified type.

        Args:
            dates (list): List of assigned and unassigned DateAssignment objects
            current_date (DateAssignment): The current date being considered for assignment
            assignment_type (str): The type of assignment to check for

        Returns:
            int: The number of days since the last assignment of the specified 
                 type or infinity if no previous assignment
        """
        last_assignment = self.get_last_assignment_date(assignment_type)
        if last_assignment is None:
            return float('inf')  # Return infinity if no previous assignment
        return sum(1 for d in dates if last_assignment < d.get_date() <= current_date.get_date())

    def get_assignment_count(self, assignment_type=None):
        if assignment_type is None:
            return len(self.assigned_dates)
        return sum(1 for assignment in self.assigned_dates if assignment.type == assignment_type)

    def get_carryover_count(self, assignment_type):
        if assignment_type not in self.carryover_dates:
            return 0
        return self.carryover_dates[assignment_type]
    