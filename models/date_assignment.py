# models/date_assignment.py

from datetime import date

class DateAssignment:
    def __init__(self, date: date, assignment_type: str, name: str = None):
        """
        Initialize a date assignment.
        
        Args:
            date: The date of the assignment
            assignment_type (str): Type of assignment (Night, Weekend, or Holiday)
            name (str, optional): Name of the assignment (primarily for holidays)
        """

        self.date = date

        # Type of assignment (Night, Weekend, or Holiday)
        self.type = assignment_type

        # Name of the assignment (primarily for holidays)
        self.name = name

        # When assigned, this will contain a physician object.
        self.assigned_physician = None

        # Whether the date is included in the calculations for the scheduler. Typically true, but can 
        # be set false when pre-assigned from prior year but needs to be output on this year's schedule.    
        self.included = True 
        
        # String used for debugging.
        self.debug_string = None

    def assign_physician(self, physician):
        """
        Assign a physician to this date.
        """
        self.assigned_physician = physician

    def get_date(self):
        """
        Returns the date of the assignment.
        """
        return self.date

    def set_debug_string(self, debug_string):
        """
        Set the debug string for the date assignment.
        """
        self.debug_string = debug_string    