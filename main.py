"""Physician Scheduling System

This module serves as the main entry point for the physician scheduling system.
It handles command line arguments, configuration loading, and orchestrates the 
scheduling process using various scheduler implementations.

The system supports scheduling physicians for different types of assignments
including nights, weekends, and holidays. It uses both round-robin and linear
programming approaches to generate fair and optimal schedules while respecting
constraints.

Key Features:
- Configurable scheduling via JSON config files
- Multiple scheduling algorithms (Round Robin, LP)
- Support for different assignment types (Night, Weekend, Holiday)
- Schedule output in multiple formats
- Debug mode for troubleshooting
"""

import random
import argparse
import json
import os
from schedulers.roundrobin_scheduler import RoundRobinScheduler
from schedulers.lp_utility import LPUtility
from input_processing.config_loader import ConfigLoader
from output_processing.schedule_printer import SchedulePrinter
from output_processing.schedule_exporter import ScheduleExporter

def load_config(config_path):
    """Load and parse the configuration file.

    Reads a JSON configuration file from the specified path and returns the parsed data.
    The configuration file contains scheduling parameters, physician data, and constraints.

    Args:
        config_path (str): Path to the JSON configuration file

    Returns:
        dict: Parsed configuration data containing scheduling parameters and constraints

    Raises:
        FileNotFoundError: If the configuration file does not exist
        json.JSONDecodeError: If the configuration file contains invalid JSON
    """
    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def main():
    """Main entry point for the physician scheduling system.

    Parses command line arguments, loads configuration, and orchestrates the scheduling process.
    Supports multiple scheduling algorithms and outputs the schedule in various formats.

    Command line arguments:
        config: Path to JSON configuration file
        --debug: Enable debug mode (default: False) 
        --output-only: Only process output from existing assignments (default: False)

    The function:
    1. Loads and validates configuration
    2. Initializes physicians and dates
    3. Creates schedulers for holidays, weekends and nights
    4. Runs the scheduling algorithms
    5. Outputs the resulting schedule

    Raises:
        ValueError: If no physicians are loaded from config
    """
    parser = argparse.ArgumentParser(description='Physician Scheduler')
    parser.add_argument('config', type=str, help='Path to the configuration file')
    parser.add_argument('-d', '--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('-o', '--output-only', action='store_true',
                       help='Process existing assignments only')

    args = parser.parse_args()
    config_path = args.config
    debug = args.debug
    print(f"Using config file: {config_path}")

    # Initialize input handler
    config_loader = ConfigLoader(config_path)
    seed = config_loader.get_seed()
    random.seed(seed)

    # Load data
    physicians = config_loader.get_physicians()
    print(f"Loaded physicians: {physicians}")
    if not physicians:
        raise ValueError("No physicians loaded from config file")
    random.shuffle(physicians)
    dates = config_loader.get_dates()

    # Create schedulers
    holiday_utility_matrix = config_loader.get_holiday_utility_matrix()
    holiday_past_assignments = config_loader.get_holiday_past_assignments()
    holiday_scheduler = LPUtility(physicians, dates, 
                                assignment_type="Holiday", 
                                utility_matrix=holiday_utility_matrix, 
                                past_assignments=holiday_past_assignments)

    constraints = config_loader.get_config_value("models", "roundrobin_scheduler", "constraints", default=[])
    weekend_scheduler = RoundRobinScheduler(physicians, dates, assignment_type="Weekend", constraints=constraints)

    night_scheduler = RoundRobinScheduler(physicians, dates, assignment_type="Night", constraints=constraints)

    # Assign dates
    holiday_scheduler.assign_dates(verbose=debug)
    weekend_scheduler.assign_dates()
    night_scheduler.assign_dates()



    # Initialize SchedulePrinter with keyword arguments
    config_dir = os.path.dirname(config_path)
    output_base_filename = os.path.splitext(os.path.basename(config_path))[0]
    output_options = config_loader.get_config_value("output_options", default={})
    schedule_printer = SchedulePrinter(config_dir, output_base_filename, **output_options)

    # Print statistics
    schedule_printer.print_assignment_statistics(dates)
    schedule_printer.print_holiday_assignments(physicians)
    schedule_printer.print_back_to_back_assignments(dates)


    schedule_exporter = ScheduleExporter(config_dir, output_base_filename, **output_options)

    # Process output options
    if output_options['output_json']:
        schedule_exporter.export_to_json(dates)

    if output_options['output_google_cal_import']:
        schedule_exporter.export_to_ics(dates)

    if output_options['output_excel']:
        schedule_exporter.export_to_excel(dates)

    if output_options['output_next_period_config']:
        # Use existing base filename with _next_schedule_period suffix
        next_config_path = f"{config_dir}/{output_base_filename}_next_schedule_period.json"
        print(f"Exporting next period config to {next_config_path}")
        schedule_exporter.export_next_config(dates, config_path, next_config_path)


if __name__ == "__main__":
    main()
