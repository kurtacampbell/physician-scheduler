"""Date Assignment Module

This module defines the DateAssignment class which represents a single date assignment
in the physician scheduling system. Date assignments can be nights, weekends, or holidays
and contain information about the assigned physician, date/time details, and other
scheduling metadata.
"""

from datetime import date, timedelta, datetime

class DateAssignment:
    """A class representing a date assignment for physician scheduling.

    This class handles assignments for different types of shifts (Night, Weekend, Holiday)
    and stores information about the assigned physician, date/time details, and other
    metadata needed for scheduling.

    Attributes:
        date (date): The date of the assignment
        type (str): Type of assignment (Night, Weekend, or Holiday)
        name (str, optional): Name of the assignment (primarily for holidays)
        start_datetime (datetime, optional): Start datetime of the assignment
        end_datetime (datetime, optional): End datetime of the assignment
        assigned_physician (Physician, optional): The physician assigned to this date
        included (bool): Whether date is included in scheduler calculations
        debug_string (str, optional): String used for debugging
    """
    def __init__(
        self,
        assignment_date: date,
        assignment_type: str,
        name: str = None,
        start_datetime: datetime = None,
        end_datetime: datetime = None
    ):
        """Initialize a date assignment.
        
        Args:
            assignment_date: The date of the assignment
            assignment_type (str): Type of assignment (Night, Weekend, or Holiday)
            name (str, optional): Name of the assignment (primarily for holidays)
            start_datetime (datetime, optional): Start datetime of the assignment
            end_datetime (datetime, optional): End datetime of the assignment
        """

        self.start_datetime = start_datetime
        self.end_datetime = end_datetime

        if start_datetime is None:
            self.date = assignment_date
        else:
            self.date = start_datetime.date()

        # Type of assignment (Night, Weekend, or Holiday)
        self.type = assignment_type

        # Name of the assignment (primarily for holidays)
        self.name = name

        # When assigned, this will contain a physician object.
        self.assigned_physician = None

        # Whether the date is included in the calculations for the scheduler. Typically
        # true, but can be set false when pre-assigned from prior year but needs to be
        # output on this year's schedule.
        self.included = True

        # String used for debugging.
        self.debug_string = None

    def assign_physician(self, physician):
        """Assign a physician to this date."""
        self.assigned_physician = physician

    def get_date(self):
        """Returns the date of the assignment."""
        return self.date

    def set_debug_string(self, debug_string):
        """Set the debug string for the date assignment."""
        self.debug_string = debug_string    

    @staticmethod
    def get_weekend_start(current_date: date) -> date:
        """Get the Friday date for a given weekend date."""
        weekday = current_date.weekday()
        if weekday == 4:  # Friday
            return current_date
        elif weekday == 5:  # Saturday
            return current_date - timedelta(days=1)
        else:  # Sunday
            return current_date - timedelta(days=2)
        