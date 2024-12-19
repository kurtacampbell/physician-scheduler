"""Output Processing Module - Schedule Exporter

This module handles exporting physician schedules to various output formats including:
- Excel spreadsheets
- JSON files 
- Google Calendar import files
- Next period configuration files

The ScheduleExporter class provides methods to export schedule data based on the output
options specified in the configuration. It handles formatting and writing the schedule
data to the appropriate file formats while maintaining consistency with the input
configuration structure.
"""

from datetime import datetime, timedelta
import json
from typing import List
import pandas as pd
from ics import Calendar, Event
from models.date_assignment import DateAssignment

class ScheduleExporter:
    """A class for exporting physician schedules to various output formats.

    This class handles exporting schedule data to Excel files, JSON files, Google Calendar 
    import files, and next period configuration files based on the output options specified 
    in the config.

    Attributes:
        config_dir (str): Directory path where config and output files are stored
        output_base_filename (str): Base filename to use for output files
        debug (bool): Whether to include debug information in exports
    """
    def __init__(self, config_dir: str, output_base_filename: str, **kwargs):
        self.config_dir = config_dir
        self.output_base_filename = output_base_filename
        self.debug = kwargs.get('debug', False)

    def export_to_excel(self, date_assignments: List[DateAssignment]) -> None:
        """
        Export the schedule to an Excel file.
        
        Args:
            date_assignments (List[DateAssignment]): List of all date assignments
        """
        # Construct output path using base filename
        output_path = f"{self.config_dir}/{self.output_base_filename}.xlsx"

        # Format the data for export
        output_assignments = []
        for assignment in date_assignments:
            output_assignments.append({
                'Date': assignment.date,
                'Type': assignment.type,
                'Day': assignment.date.strftime("%A"),
                'Physician': assignment.assigned_physician.name 
                    if assignment.assigned_physician else None,
                'Note': assignment.name if hasattr(assignment, 'name') else None,
                **({'Debug': assignment.debug_string} if self.debug else {})
            })

        # Sort assignments by date
        output_assignments.sort(key=lambda x: x['Date'])

        # Create a DataFrame
        df = pd.DataFrame(output_assignments)

        # Convert the Date column to datetime before using dt accessor
        df['Date'] = pd.to_datetime(df['Date'])
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write main schedule
            df.to_excel(writer, sheet_name='Complete Schedule')

            # Auto-adjust columns width
            worksheet = writer.sheets['Complete Schedule']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 4
                worksheet.column_dimensions[chr(65 + 1 + idx)].width = max_length 

    def export_to_ics(self, date_assignments: List[DateAssignment]) -> None:
        """Export the schedule to an ICS file.
        
        Args:
            date_assignments (List[DateAssignment]): List of all date assignments
        """
        # Create a calendar object
        calendar = Calendar()

        for assignment in date_assignments:
            if assignment.assigned_physician:   
                # Create an event object
                event = Event()
                event.name = f"{assignment.assigned_physician.name}"
                if hasattr(assignment, 'name') and assignment.name:
                    description_parts = [
                        f"{assignment.name}",
                        f"{assignment.type} Call - coverage begins at",
                        f"{assignment.start_datetime.strftime('%I:%M%p')} "
                        f"{assignment.start_datetime.strftime('%A')}",
                        "and goes through",
                        f"{assignment.end_datetime.strftime('%I:%M%p')} "
                        f"{assignment.end_datetime.strftime('%A')}."
                    ]
                    event.description = " ".join(description_parts)
                else:   
                    description_parts = [
                        f"{assignment.type} Call - coverage begins at",
                        f"{assignment.start_datetime.strftime('%I:%M%p')} "
                        f"{assignment.start_datetime.strftime('%A')}",
                        "and goes through", 
                        f"{assignment.end_datetime.strftime('%I:%M%p')} "
                        f"{assignment.end_datetime.strftime('%A')}."
                    ]
                    event.description = " ".join(description_parts)

                # Set as all-day events in PST timezone
                event.begin = assignment.start_datetime.date()
                if assignment.end_datetime.date() > assignment.start_datetime.date():
                    event.end = (assignment.end_datetime - timedelta(days=1)).date()
                else:
                    event.end = assignment.end_datetime.date()
                event.make_all_day()

                # Add the event to the calendar
                calendar.events.add(event)

        # Write the calendar to a file
        output_path = f"{self.config_dir}/{self.output_base_filename}.ics"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(calendar.serialize_iter())

    def export_to_json(self, date_assignments: List[DateAssignment]) -> None:
        """Export the schedule to a JSON file.
        
        Args:
            date_assignments (List[DateAssignment]): List of all date assignments
        """
        output_path = f"{self.config_dir}/{self.output_base_filename}_assignments.json"

        # Format the data for export
        output_data = {
            "schedule_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "assignments": []
        }

        for assignment in sorted(date_assignments, key=lambda x: x.date):
            assignment_data = {
                "date": assignment.date.strftime("%Y-%m-%d"),
                "type": assignment.type,
                "day_of_week": assignment.date.strftime("%A"),
                "start_time": assignment.start_datetime.strftime("%Y-%m-%d %H:%M"),
                "end_time": assignment.end_datetime.strftime("%Y-%m-%d %H:%M"),
                "physician": assignment.assigned_physician.name
                    if assignment.assigned_physician else None
            }

            # Add holiday name if present
            if hasattr(assignment, 'name') and assignment.name:
                assignment_data["holiday_name"] = assignment.name

            # Add debug information if enabled
            if self.debug and hasattr(assignment, 'debug_string'):
                assignment_data["debug"] = assignment.debug_string

            output_data["assignments"].append(assignment_data)

        # Write to JSON file with pretty printing
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)

    def export_next_config(self, dates, config_path, output_path):
        """
        Create next year's config file by updating holiday past assignments.
        
        Args:
            dates: List of DateAssignment objects
            config_path: Path to the current config file
            output_path: Path where the new config should be saved
        """
        # Read current config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Get holiday assignments from this run
        new_assignments = {}
        for date in dates:
            if date.type == "Holiday" and date.assigned_physician:
                if date.assigned_physician.name not in new_assignments:
                    new_assignments[date.assigned_physician.name] = {}
                new_assignments[date.assigned_physician.name][date.name] = ["1"]

        # Update past assignments
        holiday_past_assignments = config.get('models', {}).\
            get('holiday_lp', {}).\
            get('holiday_past_assignments', {})

        # Store any comment entries from holiday_past_assignments
        comments = {}
        for key, value in holiday_past_assignments.items():
            if key.startswith('_comment'):
                comments[key] = value

        # Remove comment entries
        holiday_past_assignments = {k:v for k,v in holiday_past_assignments.items()
                                  if not k.startswith('_comment')}

        # Update past assignments and add new assignments
        for physician_name, assignments in holiday_past_assignments.items():
            # Increment existing assignments by 1
            for holiday, years_list in assignments.items():
                if isinstance(years_list, list):  # Ensure we're working with a list
                    holiday_past_assignments[physician_name][holiday] = [
                        str(int(year) + 1) for year in years_list
                    ]

            # Add new assignments
            if physician_name in new_assignments:
                for holiday, years in new_assignments[physician_name].items():
                    if holiday not in holiday_past_assignments[physician_name]:
                        holiday_past_assignments[physician_name][holiday] = years
                    else:
                        holiday_past_assignments[physician_name][holiday].extend(years)
                        # Sort in place returns None, should assign sorted list instead
                        assignments = holiday_past_assignments[physician_name][holiday]
                        holiday_past_assignments[physician_name][holiday] = \
                            sorted(assignments, key=int)

        # Add comments back to holiday_past_assignments
        holiday_past_assignments = {**comments, **holiday_past_assignments}

        # Ensure the nested structure exists
        if 'models' not in config:
            config['models'] = {}
        if 'holiday_lp' not in config['models']:
            config['models']['holiday_lp'] = {}
        config['models']['holiday_lp']['holiday_past_assignments'] = holiday_past_assignments

        # Write updated config to new file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            