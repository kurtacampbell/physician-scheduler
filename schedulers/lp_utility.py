from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value, PULP_CBC_CMD
from .base_scheduler import Scheduler

class LPUtility(Scheduler):
    def __init__(self, physicians, dates, assignment_type="LP", utility_matrix=None, past_assignments=None):
        super().__init__(physicians, dates)
        self.assignment_type = assignment_type
        
        # Set utilities if provided
        self.utility_matrix = utility_matrix or {}

        # Set past assignments if provided
        # past assigments is a dictionary with the physician name as key and a dictionary with the date name as key and a list of year indexes as value.
        self.past_assignments = past_assignments or {}

    def assign_dates(self, verbose=False):
        try:
            assignable_dates = [date for date in self.dates if date.type == self.assignment_type]
            if not assignable_dates:
                return
                
            start_date = assignable_dates[0].date
            end_date = assignable_dates[-1].date

            print("--------------------------------")
            print(f"LP Scheduler:Attempting to schedule dates from {start_date} to {end_date}, total dates: {len(assignable_dates)}")
            print(f"Total Physicians: {len(self.physicians)}")
 
            # calculate physician_utilities from utility_matrix and past_assignments
            physician_utilities = {(p.name, d.date): self._calculate_physician_utility(p, d.name) for p in self.physicians for d in assignable_dates}    

            print()
            print("Physician Utilities Matrix:")
            
            # Get holiday names instead of dates for headers
            holidays = [d.name for d in assignable_dates]
            
            # Calculate column widths (max of header or physician name lengths)
            physician_width = max(len(p.name) for p in self.physicians)
            holiday_widths = [max(len(holiday), 4) for holiday in holidays]  # min width of 4 for utility values
            
            # Print header row
            print(f"{'Physician':<{physician_width}}", end="  ")
            for holiday, width in zip(holidays, holiday_widths):
                print(f"{holiday:<{width}}", end="  ")
            print()
            
            # Print each physician's utilities
            for p in self.physicians:
                print(f"{p.name:<{physician_width}}", end="  ")
                for d, width in zip(assignable_dates, holiday_widths):
                    utility = physician_utilities[p.name, d.date]
                    print(f"{utility:<{width}}", end="  ")
                print()
            

            # Create the linear programming problem
            prob = LpProblem("LP_Assignment", LpMinimize)

            # Decision Variables        
            # x[i,j] = 1 if physician i is assigned to date j, 0 otherwise
            x = LpVariable.dicts("assignment",
                               ((p.name, d.date) for p in self.physicians for d in assignable_dates),
                               cat='Binary')
            
            # Print number of decision variables
            num_variables = len(self.physicians) * len(assignable_dates)
            print()
            print(f"\nNumber of decision variables: {num_variables} ({len(self.physicians)} physicians × {len(assignable_dates)} dates)")

            # Verify that each date has at least one available physician
            for date in assignable_dates:
                available_physicians = [p for p in self.physicians if p.is_available(date.date, self.assignment_type)]
                if not available_physicians:
                    raise ValueError(f"No physicians available for {date.date} ({date.name})")
                if verbose:
                    print(f"{date.date}: {len(available_physicians)} physicians available")
            
            # Objective Function: Minimize total utility
            prob += lpSum([
                x[p.name, d.date] * physician_utilities[p.name, d.date]
                for p in self.physicians
                for d in assignable_dates
            ])
            
            # Constraints        
            # 1. Each date must be assigned to exactly one physician
            for date in assignable_dates:
                prob += lpSum([x[p.name, date.date] for p in self.physicians]) == 1
                
            # 2. Physician availability constraints
            for p in self.physicians:
                for d in assignable_dates:
                    if not p.is_available(d.date, self.assignment_type):
                        prob += x[p.name, d.date] == 0
                        print(f"LP Scheduler: Physician {p.name} is not available on {d.date}")

            # 3. No physician is assigned more than one date in each "round"
            # Define "rounds" based on the number of dates and physicians
            rounds = (len(assignable_dates) + len(self.physicians) - 1) // len(self.physicians)
            for r in range(rounds):
                for i in range(len(self.physicians)):
                    dates_in_round = assignable_dates[r*len(self.physicians):(r+1)*len(self.physicians)]
                    prob += lpSum([x[self.physicians[i].name, d.date] for d in dates_in_round]) <= 1

                    # Add constraints for adjacent dates for each date in this round
                    for d in dates_in_round:
                        # Get indices from full date list for adjacent date checks
                        current_date_index = self.dates.index(d)
                        prev_date = self.dates[current_date_index - 1] if current_date_index > 0 else None
                        next_date = self.dates[current_date_index + 1] if current_date_index < len(self.dates) - 1 else None

                        # Add constraints for adjacent dates
                        if prev_date and prev_date.assigned_physician == p:
                            prob += x[p.name, d.date] == 0
                        if next_date and next_date.assigned_physician == p:
                            prob += x[p.name, d.date] == 0

            # Add before the LP solver runs:
            if verbose:
                print("\nDebug information:")
                print(f"Attempting to schedule dates from {start_date} to {end_date}")
                print("\nPhysician assignments so far:")
                for physician in self.physicians:
                    count = len([a for a in physician.assigned_dates if a.physician == physician])
                    print(f"{physician}: {count} assignments")
                print("\nRemaining available providers:", [p for p in self.physicians if p.is_available()])

            # Solve the problem
            prob.solve(PULP_CBC_CMD(msg=verbose))
            #prob.solve()
            
            # Apply the solution
            if LpStatus[prob.status] == 'Optimal':
                print()
                print("LP Scheduler: Optimal solution found")
                for d in assignable_dates:
                    for p in self.physicians:
                        if value(x[p.name, d.date]) == 1:
                            d.assign_physician(p)
                            d.set_debug_string(self._make_debug_string(d, self.physicians, physician_utilities))
                            p.assign_date(d)
            else:
                raise ValueError("No optimal solution found")

            print()
            print("--------------------------------")

        except ValueError:
            print(f"\nFailed to find solution for period starting: {start_date}")
            print("No optimal solution could be found")
            raise


    def set_past_assignments(self, past_assignments):
        """Set the past assignments dictionary for calculating utilities.

        Args:
            past_assignments (dict): Dictionary mapping physician names to their past holiday assignments.
                                   Format: {physician_name: {holiday_name: [year_indices]}}
                                   where year_indices are strings indicating how many years ago the assignment was.
        """
        self.past_assignments = past_assignments

    def set_utility_matrix(self, utility_matrix):
        """Set the utility matrix used for calculating assignment preferences.

        Args:
            utility_matrix (dict): Dictionary mapping holiday names to their utility values.
                                 Format: {holiday_name: {"0": base_utility, "1": year_1_utility, ...}}
                                 where the keys are strings indicating years ago and values are utility modifiers.
        """
        self.utility_matrix = utility_matrix

    def _calculate_physician_utility(self, physician, date_name):
        base_utility = self.utility_matrix[date_name]["0"]

        past_assignments = self.past_assignments.get(physician.name, {}).get(date_name, [])

        total_utility = base_utility
        for year_index in past_assignments:
            if year_index in self.utility_matrix[date_name]:
                additional_utility = self.utility_matrix[date_name][year_index]
                total_utility += additional_utility

        return total_utility
    
    def _make_debug_string(self, date, physicians, physician_utilities):
        debug_str = [f"LP Scheduler Utilities for {date.date}:"]
        for physician in physicians:
            if date.name in self.utility_matrix:
                utility = physician_utilities[physician.name, date.date]
                debug_str.append(f"{physician.name}: {utility}")
            else:
                debug_str.append(f"{physician.name}: N/A - Not a holiday")
        return "\n".join(debug_str)