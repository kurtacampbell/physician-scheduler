# input/input_handler.py

import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from models.physician import Physician
from models.date_assignment import DateAssignment

class ConfigLoader:

    def __init__(self, config_path: str):
        """
        Initialize the input handler with a path to the configuration file.
        Validates that the file exists and is loadable.
        
        Args:
            config_path (str): Path to the JSON configuration file
            
        Raises:
            FileNotFoundError: If config file does not exist
            ValueError: If config file is not valid JSON
        """
        self.config_path = config_path
        
        # Validate file exists and is readable
        try:
            with open(config_path, 'r') as file:
                # Attempt to parse JSON
                self.config_data = self._strip_comments(json.load(file))
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {config_path}")
        except Exception as e:
            raise ValueError(f"Error validating config file: {str(e)}")
        
        # Save the directory path without the config file
        self.config_dir = '/'.join(config_path.split('/')[:-1])

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
        
        Returns:
            List[Physician]: List of initialized Physician objects
            
        Raises:
            ValueError: If physician data is invalid or missing required fields
        """
        physician_data = self.config_data.get('physicians', [])
        physicians = []

        # Remove comment keys from physician data
        physician_data = {k: v for k, v in physician_data.items() if not k.startswith('_comment')}

        for name, data in physician_data.items():

            # Create physician object 
            physician = Physician(name=name)
            physician.blocked_dates = {}
            physicians.append(physician)

            for key, value in data.items():    

                # Parse blocked date range if it exists
                if key == 'blocked_dates':
                    blocked_dates = {}
                    for blocked_range in value:
                        start = datetime.strptime(blocked_range['start'], '%Y-%m-%d').date()
                        end = datetime.strptime(blocked_range['end'], '%Y-%m-%d').date()
                        types = blocked_range.get('type', [])  # Get types, default to empty list if not present

                        # Add all dates in range
                        current = start
                        while current <= end:
                            if current not in blocked_dates:
                                blocked_dates[current] = []
                            # Add types to the list for this date, creating empty list if needed
                            blocked_dates[current].extend(types)
                            current += timedelta(days=1)

                    physician.blocked_dates = blocked_dates
                else:
                    # Add any other attributes to physician object
                    setattr(physician, key, value)
                
        return physicians

    def get_dates(self) -> List[DateAssignment]:
        """
        Parse and return the list of date assignments from the configuration file,
        splitting range into nights and weekends.
        
        Returns:
            List[DateAssignment]: List of all date assignments
            
        Raises:
            ValueError: If date data is invalid or in wrong format
        """
        dates_data = self.config_data.get('dates', {})
        date_assignments = []
        
        # Parse holidays first
        for holiday_data in dates_data.get('holidays', []):
            try:
                holiday_date = datetime.strptime(holiday_data['date'], '%Y-%m-%d').date()
                date_assignments.append(DateAssignment(holiday_date, 'Holiday', name=holiday_data['name']))
            except (KeyError, ValueError) as e:
                raise ValueError(f"Invalid holiday data format: {e}")

        # Parse date range
        for range_data in dates_data.get('assignement_range', []):
            try:
                start_date = datetime.strptime(range_data['start'], '%Y-%m-%d').date()
                end_date = datetime.strptime(range_data['end'], '%Y-%m-%d').date()
                
                current_date = start_date
                current_weekend = None
                
                while current_date <= end_date:
                    # Skip if it's a date or holiday already loaded
                    if any(ha.date == current_date for ha in date_assignments):
                        current_date += timedelta(days=1)
                        continue
                    
                    weekday = current_date.weekday()
                    
                    if weekday >= 4:  # Friday (4), Saturday (5), Sunday (6)
                        if current_weekend is None or current_weekend.date != DateAssignment.get_weekend_start(current_date):
                            # Create new weekend assignment starting on Friday
                            weekend_start = DateAssignment.get_weekend_start(current_date)
                            current_weekend = DateAssignment(weekend_start, 'Weekend')
                            date_assignments.append(current_weekend)
                    elif weekday <= 3:  # Monday (0) through Thursday (3)
                        date_assignments.append(DateAssignment(current_date, 'Night'))
                    
                    current_date += timedelta(days=1)
                    
            except KeyError as e:
                raise ValueError(f"Missing required field in date range: {e}")
            except ValueError as e:
                raise ValueError(f"Invalid date format in range: {e}")
            

        # Sort dates by date in ascending order
        date_assignments.sort(key=lambda x: x.date)

        return date_assignments
        
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

    def make_next_config_file(self, dates, output_path):
        """
        Create next year's config file by updating holiday past assignments.

        Consider moving this to output proceessing module.
        """
        # Read current config
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Get holiday assignments from this run
        new_assignments = {}
        for date in dates:
            if date.type == "Holiday" and date.assigned_physician:
                if date.assigned_physician.name not in new_assignments:
                    new_assignments[date.assigned_physician.name] = {}
                new_assignments[date.assigned_physician.name][date.name] = ["1"]

        # Update past assignments
        holiday_past_assignments = config['models']['holiday_lp']['holiday_past_assignments']
        
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
                    holiday_past_assignments[physician_name][holiday] = [str(int(year) + 1) for year in years_list]

            # Add new assignments
            if physician_name in new_assignments:
                for holiday, years in new_assignments[physician_name].items():
                    if holiday not in holiday_past_assignments[physician_name]:
                        holiday_past_assignments[physician_name][holiday] = years
                    else:
                        holiday_past_assignments[physician_name][holiday].extend(years)
                        holiday_past_assignments[physician_name][holiday].sort(key=lambda x: int(x))

        # Add comments back to holiday_past_assignments
        holiday_past_assignments = {**comments, **holiday_past_assignments}

        # Write updated config to new file
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=4) 


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