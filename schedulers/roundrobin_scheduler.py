from .base_scheduler import Scheduler

class RoundRobinScheduler(Scheduler):
    def __init__(self, physicians, dates, assignment_type, constraints=[]):
        super().__init__(physicians, dates)
        self.type = assignment_type
        self.constraints = constraints

    def assign_dates(self):
        """Assign shifts to physicians while ensuring fairness and accounting for availability."""

        # Calcualte total number of assignments for this type
        total_assignments = sum(1 for date in self.dates if date.type == self.type)

        # Calculate total carryover dates for all physicians for this type
        total_carryover_dates = sum(physician.get_carryover_count(self.type) for physician in self.physicians)

        # calculate base number of assignments per physician (to be adjusted by carryover date count)
        base_assignments_per_physician = (total_assignments + total_carryover_dates) / len(self.physicians)

        #for date in assignable_dates:
        for i in range(len(self.dates)):
            if self.dates[i].type == self.type:
                # This is an assignable date
                if self.dates[i].assigned_physician is None:
                    # this date is not assigned to a physician yet
                    assigned = False

                    # Get unassigned dates of current type
                    unassigned_dates = [date for date in self.dates if date.assigned_physician is None and date.type == self.type]
                    
                    # Calculate availability ratios in one pass
                    for physician in self.physicians:
                        # Calculate physician's target number of assignments for this type remaining in schedule
                        remaining_target = base_assignments_per_physician - physician.get_carryover_count(self.type) - physician.get_assignment_count(self.type)
                        
                        # Calculate remaining assignable dates in schedule period assignable to this physician
                        remaining_dates = sum(1 for date in unassigned_dates if physician.is_available(date.date, self.type))

                        # Calcualte expected number of days between each assignment
                        assignment_interval = remaining_dates / remaining_target if remaining_target > 0 else float('inf')
                        days_since_last = physician.get_days_since_last_assignment(self.dates, self.dates[i], self.type)
                        
                        # Calculate availability, ratio of days since last assignment to expected assignment interval
                        # 1 when days since last assignment is equal to expected assignment interval
                        # 0 when days since last assignment is 0
                        physician.availability = days_since_last / assignment_interval if assignment_interval > 0 else 0

                    # Sort physicians by availability ratio
                    physicians_sorted = sorted(
                        self.physicians,
                        key=lambda x: x.availability,
                        reverse=True
                    )

                    # Assign the date to the first available physician
                    for physician in physicians_sorted:
                        if not physician.is_available(self.dates[i].date, self.type):
                            continue  # skip this physician if they are not available

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