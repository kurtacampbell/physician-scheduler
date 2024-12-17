from .base_scheduler import Scheduler

class RoundRobinScheduler(Scheduler):
    def __init__(self, physicians, dates, assignment_type, constraints=[]):
        super().__init__(physicians, dates)
        self.type = assignment_type
        self.constraints = constraints

    def assign_dates(self):
        """
        Assign shifts to physicians while ensuring fairness and accounting for availability.
        """


        #for date in assignable_dates:
        for i in range(len(self.dates)):
            if self.dates[i].type == self.type:
                # This is an assignable date
                if self.dates[i].assigned_physician is None:
                    # this date is not assigned to a physician yet
                    assigned = False

                    # Get unassigned dates of current type
                    unassigned_dates = [date for date in self.dates if date.assigned_physician is None and date.type == self.type]
                    num_unassigned = len(unassigned_dates)

                    # Calculate available physicians and their metrics in one pass
                    available_count = 0
                    total_previous_assignments = 0
                    for physician in self.physicians:
                        # Count available dates for this physician
                        physician.available_dates = sum(1 for date in unassigned_dates if physician.is_available(date.date, self.type))
                        if physician.available_dates > 0:
                            available_count += 1
                        # Count previous assignments of this type
                        physician.previous_assignments = sum(1 for date in self.dates[:i] if date.assigned_physician == physician and date.type == self.type)
                        total_previous_assignments += physician.previous_assignments

                    # Calculate expected assignments and intervals
                    # Total assignments should include both previous and future assignments
                    total_assignments = total_previous_assignments + num_unassigned
                    expected_per_physician = total_assignments / len(self.physicians) if len(self.physicians) > 0 else 0

                    # Calculate availability ratios in one pass
                    for physician in self.physicians:
                        if physician.available_dates > 0:
                            # Calculate how many more assignments this physician should get
                            remaining_target = expected_per_physician - physician.previous_assignments
                            
                            # If they're behind schedule (remaining_target is high), they should get higher priority
                            assignment_interval = remaining_target / physician.available_dates if physician.available_dates > 0 else 0
                            days_since_last = physician.get_days_since_last_assignment(self.dates, self.dates[i], self.type)
                            
                            # Combine both factors: assignment ratio and days since last assignment
                            physician.availability = days_since_last / assignment_interval if assignment_interval > 0 else 0
                        else:
                            physician.availability = 0

                    # Sort physicians by availability ratio
                    physicians_sorted = sorted(
                        self.physicians,
                        key=lambda x: x.availability,
                        reverse=True
                    )

                    # Assign the date to the first available physician
                    for physician in physicians_sorted:
                        available = True
                        for constraint in self.constraints: # loop through all constraints to see if we can assign to this physician.
                            
                            # calculate the window of dates that are constrained 
                            start_window_index = max(i - constraint["distance"], 0)
                            end_window_index = min(i + constraint["distance"] + 1, len(self.dates))

                            if constraint["physician1"] == "Any":
                                # this is constraint for assignments to same physician
                                for date in self.dates[start_window_index:end_window_index]:
                                    if date.assigned_physician is not None and date.assigned_physician.name == physician.name:
                                        # physician is already assigned to something in the window
                                        available = False
                                        break

                            else:
                                # this is constraint for assignments to different physicians, check for both physicians in the constraint   
                                if constraint["physician1"] == physician.name:
                                    # this is constraint for this physician, check if the other physician is already assigned to something in the window
                                    for date in self.dates[start_window_index:end_window_index]:
                                        if date.assigned_physician is not None and date.assigned_physician.name == constraint["physician2"]:
                                            # physician is already assigned to something in the window
                                            available = False
                                            break   

                                elif constraint["physician2"] == physician.name:
                                    # this is constraint for the other physician, check if this physician is already assigned to something in the window
                                    for date in self.dates[start_window_index:end_window_index]:
                                        if date.assigned_physician is not None and date.assigned_physician.name == constraint["physician1"]:
                                            # physician is already assigned to something in the window
                                            available = False
                                            break   

                        if available:
                            self.dates[i].assign_physician(physician)
                            self.dates[i].set_debug_string(self._make_debug_string(self.dates[i], self.physicians))
                            physician.assign_date(self.dates[i])
                            assigned = True
                            break

                    if not assigned:
                        raise Exception(f"No available physician for date {self.dates[i].date}")

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