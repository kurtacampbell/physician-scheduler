# input/input_handler.py

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models.physician import Physician
from models.date_assignment import DateAssignment

class ConfigLoader:

    def __init__(self, config_path_or_data):
        """
        Initialize the input handler with either a path to the configuration file
        or the configuration data directly.

        Args:
            config_path_or_data (Union[str, dict]): Path to JSON config file or config dict

        Raises:
            FileNotFoundError: If config file does not exist
            ValueError: If config file is not valid JSON
        """
        if isinstance(config_path_or_data, dict):
            self.config_data = config_path_or_data
            self.config_path = None
            self.config_dir = ''  # Set empty string for config_dir when using dict input
        else:
            self.config_path = config_path_or_data
            # Validate file exists and is readable
            try:
                with open(config_path_or_data, 'r', encoding='utf-8') as file:
                    # Attempt to parse JSON
                    self.config_data = self._strip_comments(json.load(file))
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Configuration file not found: {config_path_or_data}") from e
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format in configuration file: {config_path_or_data}") from e

            # Only process directory path for file inputs
            self.config_dir = '/'.join(config_path_or_data.split('/')[:-1])

        # Get the output base filename from the config file, or use the current year if not specified
        self.output_base_filename = self.config_data.get('output_base_filename', f"{datetime.now().year}_schedule")

        # Get the random seed from the config file, or use 12345 if not specified
        self.random_seed = self.config_data.get('random_seed', 12345)

        # Get the debug flag from the config file, or use False if not specified
        self.debug = self.config_data.get('debug', False)

        # Get the output options from the config file
        self.output_excel = self.config_data.get('output_excel', False)
        self.output_json = self.config_data.get('output_json', False)
        self.output_google_cal_import = self.config_data.get('output_google_cal_import', False)
        self.output_next_period_config = self.config_data.get('output_next_period_config', False)    

    def get_physicians(self) -> List[Physician]:
        """
        Parse and return the list of physicians from the configuration file.
        Creates Physician objects with attributes from config including:
        - name: Physician's name
        - blocked_dates: List of date ranges when physician is unavailable
        - carryover_dates: Count of assignments carried over from previous schedule
        - Any other attributes specified in config file
        
        Returns:
            List[Physician]: List of initialized Physician objects
            
        Raises:
            ValueError: If physician data is invalid or missing required fields
            FileNotFoundError: If config file cannot be read
        """
        physician_data = self.config_data.get('physicians', {})
        physicians = []

        # Remove comment keys from physician data
        physician_data = {k: v for k, v in physician_data.items() if not k.startswith('_comment')}

        for name, data in physician_data.items():
            physician = Physician(name=name)

            # Handle blocked dates separately - ensure it's a list
            if 'blocked_dates' in data:
                blocked_dates = data['blocked_dates']
                if isinstance(blocked_dates, dict):
                    # Convert dict to list format if needed
                    blocked_dates = [blocked_dates]
                physician.add_blocked_dates(blocked_dates)

            # Handle carryover dates separately
            if 'carryover_dates' in data:
                physician.carryover_dates = data.get('carryover_dates', {})
           
            physicians.append(physician)
        
        return physicians

    def get_dates(self) -> List[DateAssignment]:
        """Parse and return the list of date assignments from the configuration file, splitting range into nights and weekends.

        Notes on date assignments: 
            - Nights are assumed to be 5pm to 8am the following day.
            - Weekends are assumed to be Friday 5pm to Sunday 8am.
            - Night and Weekend start and end times are calculated in this function.
            - Holidays are specified in the config file with a single date, and are assumed to be full days, 8am to 8am the following day.
            - If a Holiday falls on a Friday, it will be 8am to 8am the following day, and the weekend will be 8am Saturday to 8am Monday.
            - If a Holiday falls on a Saturday, the weekend shift will be considered a holiday.  There will also likely be an observed holiday on
              the Friday before, in which case both the observed holiday and the weekend from Saturday to Monday will be assigned as holiday
              shifts (needs to be specifed in the config file, else actual holiday weekend will just be assigned as a weekend call).
            - If a Holiday falls on a Sunday, there will also be an observed holiday on the Monday after. Both the observed holiday and the 
              weekend from Friday to Sunday will be assigned as holidays (needs to be specifed in the config file, else actual holiday weekend 
              will just be assigned as a weekend call).
            
        Returns:
            List[DateAssignment]: List of all date assignments
            
        Raises:
            ValueError: If date data is invalid or in wrong format
        
        """
        dates_data = self.config_data.get('dates', {})
        
        # First create all holiday assignments
        date_assignments = self._create_holiday_assignments(dates_data.get('holidays', []))
        
        # Then expand the date range into nights and weekends, respecting holidays
        date_assignments.extend(self._expand_date_range(dates_data.get('assignement_range', []), date_assignments))
        
        # Sort all assignments by date
        date_assignments.sort(key=lambda x: x.date)


        # # Print all assignments
        # for assignment in date_assignments:
        #     print(assignment.date, assignment.start_datetime, assignment.end_datetime, assignment.date.strftime('%A'), assignment.type)

        return date_assignments

    def _create_holiday_assignments(self, holiday_data: List[dict]) -> List[DateAssignment]:
        """Create holiday assignments and their associated weekend modifications.
        
        Args:
            holiday_data: List of holiday definitions from config file
            
        Returns:
            List[DateAssignment]: List of holiday and modified weekend assignments
        """
        date_assignments = []
        holidays = {}  # date -> DateAssignment mapping
        holiday_dates = {datetime.strptime(h['date'], '%Y-%m-%d').date() for h in holiday_data}
        
        for holiday in holiday_data:
            holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
            weekday = holiday_date.weekday()
            
            # Create the main holiday assignment (8am to 8am next day)
            start_dt = datetime.combine(holiday_date, datetime.strptime('08:00', '%H:%M').time())
            end_dt = datetime.combine(holiday_date + timedelta(days=1), datetime.strptime('08:00', '%H:%M').time())
            holiday_assignment = DateAssignment(holiday_date, 'Holiday', name=holiday.get('name'), 
                                             start_datetime=start_dt, end_datetime=end_dt)
            holidays[holiday_date] = holiday_assignment
            date_assignments.append(holiday_assignment)
            
            # Handle special holiday cases
            if weekday == 4:  # Friday
                next_day = holiday_date + timedelta(days=1)
                sunday = holiday_date + timedelta(days=2)
                
                # Only create weekend if neither Saturday nor Sunday are holidays
                if next_day not in holiday_dates and sunday not in holiday_dates:
                    weekend_start = holiday_date + timedelta(days=1)
                    weekend_end = holiday_date + timedelta(days=3)  # Monday
                    start_dt = datetime.combine(weekend_start, datetime.strptime('08:00', '%H:%M').time())
                    end_dt = datetime.combine(weekend_end, datetime.strptime('08:00', '%H:%M').time())
                    weekend = DateAssignment(weekend_start, 'Weekend', start_datetime=start_dt, end_datetime=end_dt)
                    date_assignments.append(weekend)
            
            elif weekday == 5:  # Saturday
                prev_day = holiday_date - timedelta(days=1)  # Friday
                next_day = holiday_date + timedelta(days=1)  # Sunday
                
                # Determine start and end dates based on adjacent holidays
                if prev_day not in holiday_dates:
                    weekend_start = prev_day  # Include Friday
                    start_dt = datetime.combine(weekend_start, datetime.strptime('17:00', '%H:%M').time())
                else:
                    weekend_start = holiday_date  # Start on Saturday
                    start_dt = datetime.combine(weekend_start, datetime.strptime('08:00', '%H:%M').time())
                    
                if next_day not in holiday_dates:
                    weekend_end = holiday_date + timedelta(days=2)  # Include through Monday
                    end_dt = datetime.combine(weekend_end, datetime.strptime('08:00', '%H:%M').time())
                else:
                    weekend_end = holiday_date + timedelta(days=1)  # End Sunday
                    end_dt = datetime.combine(weekend_end, datetime.strptime('08:00', '%H:%M').time())
                
                # Create weekend holiday if it spans any additional days
                if weekend_start < holiday_date or weekend_end > holiday_date + timedelta(days=1):
                    weekend = DateAssignment(weekend_start, 'Holiday', name=holiday.get('name'),
                                           start_datetime=start_dt, end_datetime=end_dt)
                    date_assignments.append(weekend)
                
            elif weekday == 6:  # Sunday
                prev_day = holiday_date - timedelta(days=1)  # Saturday
                prev_prev_day = holiday_date - timedelta(days=2)  # Friday
                
                # Determine start date and time based on previous holidays
                if prev_day not in holiday_dates:  # If Saturday isn't a holiday
                    if prev_prev_day not in holiday_dates:  # If Friday also isn't a holiday
                        weekend_start = prev_prev_day
                        start_dt = datetime.combine(weekend_start, datetime.strptime('17:00', '%H:%M').time())
                    else:  # Friday is a holiday
                        weekend_start = prev_day
                        start_dt = datetime.combine(weekend_start, datetime.strptime('08:00', '%H:%M').time())
                        
                    # Create weekend holiday if it would cover additional days
                    weekend = DateAssignment(weekend_start, 'Holiday', name=holiday.get('name'),
                                           start_datetime=start_dt,
                                           end_datetime=datetime.combine(holiday_date + timedelta(days=1),
                                                                       datetime.strptime('08:00', '%H:%M').time()))
                    date_assignments.append(weekend)
        
        return date_assignments

    def _expand_date_range(self, range_data: List[dict], date_assignments: List[DateAssignment]) -> List[DateAssignment]:
        """Expand date range into nights and weekends, respecting holidays.
        
        Args:
            range_data: List of date range definitions from config file
            date_assignments: List of existing date assignments
            
        Returns:
            List[DateAssignment]: List of expanded date assignments
        """
        expanded_date_assignments = []
        # Create a set of dates that already have assignments for efficient lookup
        existing_dates = {da.date for da in date_assignments}
        
        for range_item in range_data:
            start_date = datetime.strptime(range_item['start'], '%Y-%m-%d').date()
            end_date = datetime.strptime(range_item['end'], '%Y-%m-%d').date()
            
            current_date = start_date
            current_weekend = None
            
            while current_date <= end_date:
                # Skip if date already has an assignment or is covered by a holiday
                if current_date in existing_dates or any(
                    da.date <= current_date < da.end_datetime.date()  
                    for da in date_assignments if da.type == "Holiday"
                ):
                    current_date += timedelta(days=1)
                    continue
                
                weekday = current_date.weekday()
                
                if weekday >= 4:  # Friday (4), Saturday (5), Sunday (6)
                    if current_weekend is None or current_weekend.date != DateAssignment.get_weekend_start(current_date):
                        # Check if any day in the weekend is a holiday before creating weekend assignment
                        weekend_start = DateAssignment.get_weekend_start(current_date)
                        weekend_dates = {weekend_start + timedelta(days=i) for i in range(3)}  # Fri, Sat, Sun
                        if not any(d in existing_dates for d in weekend_dates):
                            start_datetime = datetime.combine(weekend_start, datetime.strptime('17:00', '%H:%M').time())
                            end_datetime = datetime.combine(weekend_start + timedelta(days=3), datetime.strptime('08:00', '%H:%M').time())
                            current_weekend = DateAssignment(weekend_start, 'Weekend', 
                                                          start_datetime=start_datetime,
                                                          end_datetime=end_datetime)
                            expanded_date_assignments.append(current_weekend)
                elif weekday <= 3:  # Monday (0) through Thursday (3)
                    # Create night assignment if date isn't a holiday
                    start_datetime = datetime.combine(current_date, datetime.strptime('17:00', '%H:%M').time())
                    end_datetime = datetime.combine(current_date + timedelta(days=1), datetime.strptime('08:00', '%H:%M').time())
                    expanded_date_assignments.append(DateAssignment(current_date, 'Night', 
                                                                 start_datetime=start_datetime, 
                                                                 end_datetime=end_datetime))
                
                current_date += timedelta(days=1)
                
        return expanded_date_assignments
        
    def get_excel_path(self) -> str:
        """
        Get the output file path from the configuration file.
        If not specified, returns a default filename based on the current year.
        
        Returns:
            str: Path where the schedule should be exported
        """
        return self.config_data.get('excel_path', f"schedule_{datetime.now().year}.xlsx")
        
    def get_seed(self) -> int:
        """
        Get the seed from the configuration file.
        """
        return self.config_data.get('random_seed', 12345)
        
    def get_holiday_utility_matrix(self) -> Dict[str, Dict[str, int]]:
        """ 
        Get the holiday utility matrix from the configuration file.
        """
        return_dict = self.config_data.get('models', {}).get('holiday_lp', {}).get('holiday_default_utility_matrix', {})   
        return {k: v for k, v in return_dict.items() if not k.startswith('_comment')}
    
    def get_holiday_past_assignments(self) -> Dict[str, Dict[str, List[int]]]:
        """
        Get the holiday past assignments from the configuration file.
        """ 
        return self.config_data.get('models', {}).get('holiday_lp', {}).get('holiday_past_assignments', {})     

    def get_holiday_default_utility(self) -> int:
        """
        Get the holiday default utility from the configuration file.
        """
        return self.get_config_value("models", "holiday_lp", "holiday_default_utility", default=10)

    def _strip_comments(self, data):
        """Recursively removes all keys that start with '_comment' from nested dictionaries"""
        if not isinstance(data, dict):
            return data
            
        result = {k: v for k, v in data.items() if not k.startswith('_comment')}
        for key, value in result.items():
            if isinstance(value, dict):
                result[key] = self._strip_comments(value)
        return result

    def get_config_value(self, *keys: str, default: Any = None) -> Any:
        """
        Get a value from nested dictionary keys in the config file.
        
        Args:
            *keys: Variable number of string keys representing the path to the value
            default: Default value to return if the path doesn't exist
            
        Returns:
            Any: The value at the specified path, or the default if not found
            
        Example:
            # For config structure like:
            # {
            #     "models": {
            #         "holiday_lp": {
            #             "holiday_default_utility": 10
            #         }
            #     }
            # }
            # Call with:
            # get_config_value("models", "holiday_lp", "holiday_default_utility", default=5)
        """
        current = self.config_data
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default