# main.py

from schedulers.roundrobin_scheduler import RoundRobinScheduler
from schedulers.lp_utility import LPUtility
from input_processing.config_loader import ConfigLoader
from output_processing.schedule_printer import SchedulePrinter
import random
import argparse
import json

# TODO: Add logging
# TODO: Enable preassigned dates
# TODO: Enable output range vs. assignment range

def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

def main():
    parser = argparse.ArgumentParser(description='Physician Scheduler')
    parser.add_argument('config', type=str, help='Path to the configuration file')
    parser.add_argument('--debug', type=bool, required=False, default=False, help='Enable debug mode')
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
    random.shuffle(physicians)
    dates = config_loader.get_dates()

    # Create schedulers
    holiday_utility_matrix = config_loader.get_holiday_utility_matrix()
    holiday_past_assignments = config_loader.get_holiday_past_assignments()
    holiday_default_utility = config_loader.get_holiday_default_utility()

    # Get constraints from config file
    constraints = config_loader.get_config_value("models", "roundrobin_scheduler", "constraints", default=[])

    # Create schedulers
    holiday_scheduler = LPUtility(physicians, dates, 
                                assignment_type="Holiday", 
                                utility_matrix=holiday_utility_matrix, 
                                past_assignments=holiday_past_assignments)
    weekend_scheduler = RoundRobinScheduler(physicians, dates, assignment_type="Weekend", constraints=constraints)
    night_scheduler = RoundRobinScheduler(physicians, dates, assignment_type="Night", constraints=constraints)

    # Assign dates
    holiday_scheduler.assign_dates(verbose=debug)
    weekend_scheduler.assign_dates()
    night_scheduler.assign_dates()

    # Get the required configuration for SchedulePrinter
    output_options = {
        'config_dir': config_loader.config_dir,
        'output_base_filename': config_loader.output_base_filename,
        'debug': config_loader.debug
    }

    # Initialize SchedulePrinter with keyword arguments
    schedule_printer = SchedulePrinter(**output_options)

    # Print statistics
    schedule_printer.print_assignment_statistics(dates)
    schedule_printer.print_holiday_assignments(physicians)
    schedule_printer.print_back_to_back_assignments(dates)

    # Process output options
    if config_loader.output_excel:
        schedule_printer.export_to_excel(dates)

    """
    if output_options['output_json']:
        schedule_printer.export_to_json(dates, debug=debug)

    if output_options['output_google_cal']:
        schedule_printer.export_to_google_cal(dates, debug=debug)

    # Output the schedule
    #SchedulePrinter.print_chronological_schedule(physicians)

    SchedulePrinter.print_assignment_statistics(dates)
    SchedulePrinter.print_holiday_assignments(physicians)
    SchedulePrinter.print_back_to_back_assignments(dates)

    # Export to Excel
    SchedulePrinter.export_to_excel(dates, excel_file, debug=debug)

    # Make next config file
    config_loader.make_next_config_file(dates, 'config/2026_config.json')

    """

if __name__ == "__main__":
    main()