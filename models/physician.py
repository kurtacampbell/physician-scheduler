# models/physician.py

from datetime import date

class Physician:
    def __init__(self, name, blocked_dates=None):
        self.name = name
        self.blocked_dates = blocked_dates
        self.assigned_dates = []  # List of DateAssignment objects

    def is_available(self, check_date: date, assignment_type: str = None) -> bool:
        """
        Check if the physician is available on a given date for a specific assignment type.
        
        Args:
            check_date (date): The date to check availability for
            assignment_type (str, optional): The type of assignment to check. If None, checks for any block.
        
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
        """
        Assign a date to the physician.
        """
        self.assigned_dates.append(date_assignment)

    def calculate_total_available_dates(self, dates):
        """
        Calculate the total number of dates the physician is available for.
        """
        self.total_available_dates = sum(1 for date in dates if self.is_available(date))

    def get_last_assignment_date(self, assignment_type):
        """
        Returns the date of the physician's most recent assignment.
        
        Returns:
            datetime.date: The date of the last assignment
            None: If the physician has no assignments of the specified type
        """
        matching_assignments = [assignment.date for assignment in self.assigned_dates 
                              if assignment.type == assignment_type]
        return max(matching_assignments) if matching_assignments else None

    def get_days_since_last_assignment(self, dates, current_date, assignment_type):
        """
        Get the number of days since the physician's last assignment of the specified type.

        Args:
            dates (list): List of assigned and unassigned DateAssignment objects
            current_date (DateAssignment): The current date being considered for assignment
            assignment_type (str): The type of assignment to check for

        Returns:
            int: The number of days since the last assignment of the specified type or infinity if no previous assignment
        """
        last_assignment = self.get_last_assignment_date(assignment_type)
        if last_assignment is None:
            return float('inf')  # Return infinity if no previous assignment
        return sum(1 for d in dates if last_assignment < d.get_date() < current_date.get_date())