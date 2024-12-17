# Physician Scheduler

A scheduling system for managing physician on-call assignments using multiple algorightms for assignment, and allowing for flexible configuration of constraints. In the specific use case for which it was developed, it schedules night, weekend, and holiday coverage for a group of physicians with responsiblity to cover a hospital's specialty service.

## Features

- **Multiple Assignment Types**: Supports various shift types:
  - Night, Weekend, and Holiday coverage as currently implemented
  - Additional assignment types can be added by modifying config_loader.py and main.py
- **Fair Distribution**: Ensures equitable distribution of assignments among physicians using two assignment algorithms:
  - Linear Programming (LP) for holiday assignments, minimizing reassignment of the same holiday to same physician year to year.
  - Round Robin (RR) for night and weekend assignments, rotating through physicians depending on availability, last assignment, and estimated total assignments.
- **Constraint Handling**:
  - Prevents back-to-back assignments, or assigments between two physicians within a given number of assignment events, as configured
  - Allows physicians to block dates for pre-existing commitments
- **Multiple Output Formats**:
  - Excel file with chronological schedule
  - JSON with assigned dates
  - Updated config file to be used the following year (or scheduling period)
- **Flexible Configuration**: Easy to customize rules and constraints in JSON format

## Modifying to your own use case

- Currently, config_loader.py and main.py are tightly coupled to the specific use case for which it was developed. Config_loader.py looks for a date range to split into nights and weekends, and looks for a specific key in the config file to enumerate holidays. To add assignment types, modify config_loader.py and main.py to add the new assignment type.
- RoundRobinScheduler will schedule assignments based on type. It uses the config section models/roundrobin_scheduler/constraints to enumerate constraints. A constraint with physician1 as "Any" will apply to all physicians. A constraint with physician1 as a specific physician will apply to that physician and is bidirectional, i.e. assignments to both physician1 and physician2 will be prevented within the distance specified.
- LPUtility will schedule assignments based on type. It uses the config section models/holiday_lp/holiday_default_utility_matrix to store the utility matrix. The utility matrix is a dictionary with the holiday name as the key and the value is a dictionary with the year_index as the key and utility as the value. The year_index represents how many years ago a provider was assigned to this holiday.
- The config file is organized by year, with each year having its own config file. This allows for easy modification of the config file for each year or scheduling period. It is suggested to create a new directory for each year or scheduling period, and create a new config file for each year.


## Installation

1. Clone the repository:

```bash 
git clone https://github.com/kurtacampbell/physician-scheduler.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Set up scheduling parameters in a JSON file, see `sample_config.json`
3. Run the scheduler:

```bash
python main.py sample_config.json
```
output files will be created in the same directory as the config file.


## Project Structure

```
physician-scheduler/
├── config/                 # Configuration files, it is suggested to create a new directory for each year or scheduling period
├── models/                 # Core data models
├── schedulers/            # Scheduling algorithms
├── tests/                # Unit tests
├── input_processing/     # Input processing, load config file and data
└── output_processing/     # Output processing, export to excel, json, and updated config file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU Affero General Public License v3 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.

## Authors

- Kurt Campbell

## Acknowledgments

- Thanks to all contributors and users of this project

## Future Work

The following features and improvements are planned for future releases:
- Make sure output files end up in same directory as config file per readme.
- Unless the number of assignable dates for a given type is divisible by number of physicians, there will be unequal assignments. The max difference should be 1. Fix that.
- Add carryforward data to each physician to adjust future year's assignments based on this year's assignments.

- Update excel output to include a tab with summary statistics for each physician, and a tab with assignments ready for google calendar import.
- Output assignments to a JSON that can be reloaded into the system for further processing or analysis.
- Allow pre-assigned dates in config file that are counted towards total assignments for a given physician.
- Consider extending LP model to handle night and weekend coveage optimizing for distance between assignments for a given physician.
- Abstract the assignment types to minimize code changes for new assignment types.

Suggestions and contributions for any of these features are welcome!



