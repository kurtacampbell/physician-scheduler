from .base_scheduler import Scheduler

class AssignmentScheduler(Scheduler):
    def __init__(self, physicians, dates, assignment_type):
        super().__init__(physicians, dates)
        self.type = assignment_type

    def assign_dates(self):
        """
        Assign shifts to physicians while ensuring fairness and accounting for availability.
        """

        # Calculate expected assignments per physician for this assignment type
        available_physicians = sum(1 for physician in self.physicians if any(physician.is_available(date.date, self.type) for date in self.dates))
        unassigned_dates = sum(1 for date in self.dates if date.assigned_physician is None and date.type == self.type)
        expected_assignments = unassigned_dates / available_physicians if available_physicians > 0 else 0

        # Calculate assignment interval for each physician and store it in the physician object
        for physician in self.physicians:
            available_dates = sum(1 for date in self.dates if physician.is_available(date.date, self.type))
            physician.assignment_interval = available_dates / expected_assignments if expected_assignments > 0 else float('inf')

        # Assign dates
        assignable_dates = [d for d in self.dates if d.type == self.type]
        for date in assignable_dates:
            assigned = False

            # Calculate and store availability ratio for each physician
            for physician in self.physicians:
                days_since_last_assignment = physician.get_days_since_last_assignment(self.dates, date, self.type)
                physician.availability = days_since_last_assignment / physician.assignment_interval if physician.assignment_interval > 0 else float('inf')
            
            # Sort physicians based on stored availability ratio
            physicians_sorted = sorted(
                self.physicians,
                key=lambda x: x.availability,
                reverse=True
            )

            # Get indices from full date list
            current_date_index = self.dates.index(date)
            prev_date = self.dates[current_date_index - 1] if current_date_index > 0 else None
            next_date = self.dates[current_date_index + 1] if current_date_index < len(self.dates) - 1 else None

            for physician in physicians_sorted:
                # Check if physician is available and doesn't have adjacent assignments
                if (physician.is_available(date.date, self.type) and
                    not self._has_adjacent_assignments(physician, date)):
                    date.assign_physician(physician)
                    date.set_debug_string(self._make_debug_string(date, self.physicians))
                    physician.assign_date(date)
                    assigned = True
                    break

            if not assigned:
                raise Exception(f"No available physician for date {date.date}")

    def _make_debug_string(self, date, physicians):
        """
        Create a debug string for a given date and list of physicians.
        """
        return f"Date: {date.date}, Physicians: {[(physician.name, physician.availability) for physician in physicians]}" 

    def _has_adjacent_assignments(self, physician, current_date):
        """
        Check if physician has any assignments on adjacent dates by checking their assigned_dates directly.
        """
        current_date = current_date.date  # Get the datetime.date object
        
        # Check physician's assigned dates for any adjacent dates
        for assigned_date in physician.assigned_dates:
            assigned_date = assigned_date.date  # Get the datetime.date object
            days_difference = abs((current_date - assigned_date).days)
            if days_difference == 1:  # Adjacent date found
                return True

        return False