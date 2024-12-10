# main.py

from schedulers.assignment_scheduler import AssignmentScheduler
from schedulers.lp_scheduler import LPScheduler
from input_processing.config_loader import ConfigLoader
from output_processing.schedule_printer import SchedulePrinter
import random

# TODO: Add command line arguments for config file, excel file, and seed
# TODO: Add logging
# TODO: Enable preassigned dates
# TODO: Enable output range vs. assignment range
# TODO: create new config file for 2026


def main():
    debug = False

    # Initialize input handler
    config_loader = ConfigLoader('config/2025_config.json')
    excel_file = config_loader.get_excel_path()
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

    holiday_scheduler = LPScheduler(physicians, dates, assignment_type="Holiday", utility_matrix=holiday_utility_matrix, past_assignments=holiday_past_assignments)
    weekend_scheduler = AssignmentScheduler(physicians, dates, assignment_type="Weekend")
    night_scheduler = AssignmentScheduler(physicians, dates, assignment_type="Night")

    # Assign dates
    holiday_scheduler.assign_dates(verbose=debug)
    weekend_scheduler.assign_dates()
    night_scheduler.assign_dates()

    # Output the schedule
    #SchedulePrinter.print_chronological_schedule(physicians)

    # Print statistics
    SchedulePrinter.print_assignment_statistics(dates)
    SchedulePrinter.print_holiday_assignments(physicians)
    SchedulePrinter.print_back_to_back_assignments(dates)

    # Export to Excel
    SchedulePrinter.export_to_excel(dates, excel_file, debug=debug)

    # Make next config file
    config_loader.make_next_config_file(dates, 'config/2026_config.json')

if __name__ == "__main__":
    main()