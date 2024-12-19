"""Output Processing Module - Schedule Printer

This module provides methods to print physician schedules in various formats, including:
- Chronological schedule
- Back-to-back assignments
- Adjacent assignments between two specific physicians
- Holiday assignments
- Assignment statistics
"""

from typing import List
from models.physician import Physician
from models.date_assignment import DateAssignment


class SchedulePrinter:
    def __init__(self, config_dir: str, output_base_filename: str, **kwargs):
        self.config_dir = config_dir
        self.output_base_filename = output_base_filename
        self.debug = kwargs.get('debug', False)

    @staticmethod
    def print_chronological_schedule(physicians: List[Physician]) -> None:
        """Print all assignments chronologically.
        
        Args:
            physicians (List[Physician]): List of physicians with their assignments
        """
        # Collect all assignments
        all_assignments = []
        for physician in physicians:
            for assignment in physician.assigned_dates:
                all_assignments.append({
                    'date': assignment.date,
                    'type': assignment.type,
                    'physician': physician.name,
                    'holiday_name': assignment.name if hasattr(assignment, 'name') else None
                })

        # Sort by date
        all_assignments.sort(key=lambda x: x['date'])

        # Print assignments
        print("\nComplete Schedule (Chronological Order):")
        print("----------------------------------------")
        current_month = None

        for assignment in all_assignments:
            # Print month header if it's a new month
            assignment_month = assignment['date'].strftime("%B %Y")
            if assignment_month != current_month:
                current_month = assignment_month
                print(f"\n{current_month}")
                print("----------------------------------------")

            # Format the assignment line
            date_str = assignment['date'].strftime("%a, %b %d")
            assignment_str = f"{date_str}: {assignment['type']}"
            if assignment['holiday_name']:
                assignment_str += f" ({assignment['holiday_name']})"
            assignment_str += f" - {assignment['physician']}"

            print(assignment_str) 

    @staticmethod
    def print_back_to_back_assignments(date_assignments: List[DateAssignment]) -> None:
        """Print all instances of back-to-back assignments in the schedule.
        
        Args:
            date_assignments (List[DateAssignment]): List of date assignments to analyze
        """
        # Sort assignments by date
        sorted_assignments = sorted(date_assignments, key=lambda x: x.date)

        # Track back to back assignments
        back_to_back = []

        # Check each adjacent pair of assignments
        for i in range(len(sorted_assignments)-1):
            current = sorted_assignments[i]
            next_day = sorted_assignments[i+1]

            # Skip if either assignment has no physician
            if not current.assigned_physician or not next_day.assigned_physician:
                continue

            # Check if dates are assigned to the same physician
            if current.assigned_physician.name == next_day.assigned_physician.name:
                back_to_back.append({
                    'physician': current.assigned_physician.name,
                    'first_date': current.date,
                    'second_date': next_day.date,
                    'types': f"{current.type} -> {next_day.type}"
                })

        # Print results
        if back_to_back:
            print("\nBack-to-back Assignments:")
            print("-------------------------------")
            for entry in back_to_back:
                print(f"Physician: {entry['physician']}")
                print(f"Dates: {entry['first_date']} -> {entry['second_date']}")
                print(f"Types: {entry['types']}")
                print("-------------------------------")

            print(f"\nBack-to-back Assignments Found: {len(back_to_back)}")

    @staticmethod
    def print_adjacent_assignments_between_physicians(
        date_assignments: List[DateAssignment],
        physician1: Physician,
        physician2: Physician
    ) -> None:
        """Print all instances where two specific physicians have adjacent assignments.
        
        Args:
            date_assignments (List[DateAssignment]): List of date assignments to analyze
            physician1 (Physician): First physician to check
            physician2 (Physician): Second physician to check
        """
        # Sort assignments by date
        sorted_assignments = sorted(date_assignments, key=lambda x: x.date)

        # Track adjacent assignments
        adjacent_assignments = []

        # Check each adjacent pair of assignments
        for i in range(len(sorted_assignments)-1):
            current = sorted_assignments[i]
            next_day = sorted_assignments[i+1]

            # Skip if either assignment has no physician
            if not current.assigned_physician or not next_day.assigned_physician:
                continue

            # Check if dates involve both physicians
            is_physician1_then_2 = (current.assigned_physician == physician1 and
                                  next_day.assigned_physician == physician2)
            is_physician2_then_1 = (current.assigned_physician == physician2 and
                                  next_day.assigned_physician == physician1)
            if is_physician1_then_2 or is_physician2_then_1:
                adjacent_assignments.append({
                    'first_physician': current.assigned_physician.name,
                    'second_physician': next_day.assigned_physician.name,
                    'first_date': current.date,
                    'second_date': next_day.date,
                    'types': f"{current.type} -> {next_day.type}"
                })

        # Print results
        if adjacent_assignments:
            print(f"\nAdjacent Assignments between {physician1.name} and {physician2.name}:")
            print("-------------------------------")
            for entry in adjacent_assignments:
                print(f"Sequence: {entry['first_physician']} -> {entry['second_physician']}")
                print(f"Dates: {entry['first_date']} -> {entry['second_date']}")
                print(f"Types: {entry['types']}")
                print("-------------------------------")

            print(f"\nAdjacent Assignments Found: {len(adjacent_assignments)}")


    @staticmethod
    def print_holiday_assignments(physicians: List[Physician]) -> None:
        """Print all holiday assignments.
        
        Args:
            physicians (List[Physician]): List of physicians with their assignments
        """
        holiday_assignments = [date for physician in physicians
                             for date in physician.assigned_dates
                             if date.type == "Holiday"]
        holiday_assignments.sort(key=lambda x: x.date)

        print("\nHoliday Assignments:")
        print("-------------------------------")
        for holiday in holiday_assignments:
            print(f"{holiday.name} ({holiday.date}): {holiday.assigned_physician.name}")
        print("-------------------------------")

    @staticmethod
    def print_assignment_statistics(dates: List[DateAssignment]) -> None:
        """
        Print statistics about assignments for each physician in a table format.
        
        Args:
            dates (List[DateAssignment]): List of all date assignments
        """
        # Initialize statistics dictionary
        stats = {}

        # Count assignments for each physician
        for date in dates:
            if not date.assigned_physician:
                continue

            physician_name = date.assigned_physician.name
            if physician_name not in stats:
                stats[physician_name] = {
                    "Total": 0
                }

            # Add new type if not seen before
            if date.type not in stats[physician_name]:
                stats[physician_name][date.type] = 0

            stats[physician_name][date.type] += 1
            stats[physician_name]["Total"] += 1

        # Get all unique assignment types
        assignment_types = set()
        for physician_stats in stats.values():
            assignment_types.update(physician_stats.keys())
        assignment_types.remove("Total")  # Remove Total from types list
        assignment_types = sorted(assignment_types)

        # Print header
        print("\nAssignment Statistics:")
        print("-" * (20 + 12 * (len(assignment_types) + 1)))  # +1 for Total column

        # Print column headers
        header = "Physician".ljust(20)
        for type_name in assignment_types:
            header += type_name.center(12)
        header += "Total".center(12)
        print(header)
        print("-" * (20 + 12 * (len(assignment_types) + 1)))

        # Print each physician's stats
        for physician in sorted(stats.keys()):
            row = physician.ljust(20)
            for assignment_type in assignment_types:
                count = stats[physician].get(assignment_type, 0)
                row += str(count).center(12)
            row += str(stats[physician]["Total"]).center(12)
            print(row)

        print("-" * (20 + 12 * (len(assignment_types) + 1)))
