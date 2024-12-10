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
        
        Args:
            config_path (str): Path to the JSON configuration file
        """
        self.config_path = config_path

    def load_config(self) -> tuple[List[Physician], List[DateAssignment]]:
        """
        Load and parse all data from the configuration file.
        
        Returns:
            tuple: (List of Physicians, List of date assignments)
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            physicians = self._parse_physicians(data.get('physicians', []))
            dates = self._parse_dates(data.get('dates', {}))
            
            return physicians, dates
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")

    def get_physicians(self) -> List[Physician]:
        """
        Returns the list of physicians from the configuration file.
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            physicians = self._parse_physicians(data.get('physicians', []))
            
            return physicians
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")

    def get_dates(self) -> List[DateAssignment]:
        """
        Returns the list of date assignments from the configuration file.
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            physicians = self._parse_physicians(data.get('physicians', []))
            dates = self._parse_dates(data.get('dates', {}))
            
            return dates
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")

    def _parse_physicians(self, physician_data: Dict[str, Any]) -> List[Physician]:
        """
        Parse physician data from the configuration.
        
        Args:
            physician_data (Dict[str, Any]): Dictionary of physician configurations with names as keys
            
        Returns:
            List[Physician]: List of initialized Physician objects
        """
        physicians = []

        # Remove comment keys from physician data
        physician_data = {k: v for k, v in physician_data.items() if not k.startswith('_comment')}

        for name, data in physician_data.items():
            try:
                # Parse blocked date range
                blocked_dates = {}
                if 'blocked_dates' in data:
                    for block in data['blocked_dates']:
                        start = datetime.strptime(block['start'], '%Y-%m-%d').date()
                        end = datetime.strptime(block['end'], '%Y-%m-%d').date()
                        types = block.get('type', [])  # Get types, default to empty list if not present

                        # Add all dates in range
                        current = start
                        while current <= end:
                            if current not in blocked_dates:
                                blocked_dates[current] = []
                            blocked_dates[current].extend(types)
                            current += timedelta(days=1)

                # Create physician object
                physician = Physician(
                    name=name,
                    blocked_dates=blocked_dates,
                    carryover_data=data.get('carryover_data', {})
                )
                physicians.append(physician)
                
            except KeyError as e:
                raise ValueError(f"Missing required field for physician: {e}")
            except ValueError as e:
                raise ValueError(f"Invalid date format in blocked dates for {name}: {e}")
                
        return physicians

    def _parse_dates(self, dates_data: Dict[str, Any]) -> List[DateAssignment]:
        """
        Parse date assignments from the configuration, splitting range into nights and weekends.
        
        Returns:
            List[DateAssignment]: List of all date assignments
        """
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
                        if current_weekend is None or current_weekend.date != self._get_weekend_start(current_date):
                            # Create new weekend assignment starting on Friday
                            weekend_start = self._get_weekend_start(current_date)
                            current_weekend = DateAssignment(weekend_start, 'Weekend')
                            date_assignments.append(current_weekend)
                    elif weekday <= 3:  # Monday (0) through Thursday (3)
                        date_assignments.append(DateAssignment(current_date, 'Night'))
                    
                    current_date += timedelta(days=1)
                    
            except KeyError as e:
                raise ValueError(f"Missing required field in date range: {e}")
            except ValueError as e:
                raise ValueError(f"Invalid date format in range: {e}")
                
        return date_assignments

    @staticmethod
    def _get_weekend_start(current_date: date) -> date:
        """
        Get the Friday date for a given weekend date.
        """
        weekday = current_date.weekday()
        if weekday == 4:  # Friday
            return current_date
        elif weekday == 5:  # Saturday
            return current_date - timedelta(days=1)
        else:  # Sunday
            return current_date - timedelta(days=2)
        
    def get_excel_path(self) -> str:
        """
        Get the output file path from the configuration file.
        If not specified, returns a default filename based on the current year.
        
        Returns:
            str: Path where the schedule should be exported
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            # Return the specified output file or generate a default name
            return data.get('excel_path', f"schedule_{datetime.now().year}.xlsx")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")
        
    def get_seed(self) -> int:
        """
        Get the seed from the configuration file.
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            # Return the specified output file or generate a default name
            return data.get('random_seed', 12345)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")
        
    def get_holiday_utility_matrix(self) -> Dict[str, Dict[str, int]]:
        """ 
        Get the holiday utility matrix from the configuration file.
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)

            return_dict = data.get('models').get('holiday_lp').get('holiday_utility_matrix', {})   
            # Remove any keys that start with _comment
            return_dict = {k: v for k, v in return_dict.items() if not k.startswith('_comment')}

            return return_dict

        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")
    
    def get_holiday_past_assignments(self) -> Dict[str, Dict[str, List[int]]]:
        """
        Get the holiday past assignments from the configuration file.
        """ 
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            return data.get('models').get('holiday_lp').get('holiday_past_assignments', {})     

        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")

    def get_holiday_default_utility(self) -> int:
        """
        Get the holiday default utility from the configuration file.
        """
        try:
            with open(self.config_path, 'r') as file:
                data = json.load(file)
            
            return data.get('models').get('holiday_lp').get('holiday_default_utility', 10)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {self.config_path}")  


    def make_next_config_file(self, dates, output_path):
        """
        Create next year's config file by updating holiday past assignments.
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