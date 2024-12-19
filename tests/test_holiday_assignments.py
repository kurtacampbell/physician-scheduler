from datetime import datetime, date
import pytest
from input_processing.config_loader import ConfigLoader
from models.date_assignment import DateAssignment

@pytest.fixture
def config_loader():
    sample_config = {
        "dates": {
            "assignement_range": [],
            "holidays": []
        }
    }
    return ConfigLoader(sample_config)

def test_basic_holiday_creation(config_loader):
    """Test creation of a basic holiday on a weekday"""
    holiday_data = [{
        "date": "2025-01-01",  # Wednesday
        "name": "New Year's Day"
    }]
    
    assignments = config_loader._create_holiday_assignments(holiday_data)
    
    assert len(assignments) == 1
    holiday = assignments[0]
    assert holiday.type == 'Holiday'
    assert holiday.name == "New Year's Day"
    assert holiday.start_datetime.hour == 8  # 8 AM
    assert holiday.end_datetime.hour == 8    # 8 AM next day
    assert holiday.end_datetime.date() == date(2025, 1, 2)

def test_friday_holiday(config_loader):
    """Test holiday on Friday modifies weekend timing"""
    holiday_data = [{
        "date": "2025-07-04",  # Friday
        "name": "Independence Day"
    }]
    
    assignments = config_loader._create_holiday_assignments(holiday_data)
    
    # Should have holiday and modified weekend
    assert len(assignments) == 2
    
    holiday = next(a for a in assignments if a.date == date(2025, 7, 4))
    weekend = next(a for a in assignments if a.date == date(2025, 7, 5))
    
    # Verify holiday timing
    assert holiday.type == 'Holiday'
    assert holiday.start_datetime.hour == 8  # 8 AM Friday
    assert holiday.end_datetime.hour == 8    # 8 AM Saturday
    
    # Verify weekend timing
    assert weekend.type == 'Weekend'
    assert weekend.start_datetime.hour == 8  # 8 AM Saturday
    assert weekend.end_datetime.hour == 8    # 8 AM Monday

def test_saturday_holiday(config_loader):
    """Test holiday on Saturday modifies weekend"""
    holiday_data = [{
        "date": "2025-07-05",  # Saturday
        "name": "Holiday on Saturday"
    }]
    
    assignments = config_loader._create_holiday_assignments(holiday_data)
    
    # Should have main holiday and weekend holiday
    assert len(assignments) == 2
    
    for a in assignments:
        print(a.type, a.name, a.date.strftime('%A'), a.start_datetime, a.end_datetime)

    holiday = next(a for a in assignments if a.type == 'Holiday' and not a.name.endswith('Weekend'))
    weekend = next(a for a in assignments if a.name.endswith('Weekend'))
    
    # Verify holiday
    assert holiday.start_datetime.hour == 8  # 8 AM Saturday
    assert holiday.end_datetime.hour == 8    # 8 AM Sunday
    
    # Verify weekend holiday
    assert weekend.type == 'Holiday'
    assert weekend.start_datetime.hour == 17  # 5 PM Friday
    assert weekend.end_datetime.hour == 8     # 8 AM Monday

def test_sunday_holiday(config_loader):
    """Test holiday on Sunday modifies weekend"""
    holiday_data = [{
        "date": "2025-07-06",  # Sunday
        "name": "Holiday on Sunday"
    }]
    
    assignments = config_loader._create_holiday_assignments(holiday_data)
    
    # Should have main holiday and weekend holiday
    assert len(assignments) == 2
    
    holiday = next(a for a in assignments if a.type == 'Holiday' and not a.name.endswith('Weekend'))
    weekend = next(a for a in assignments if a.name.endswith('Weekend'))
    
    # Verify holiday
    assert holiday.start_datetime.hour == 8  # 8 AM Sunday
    assert holiday.end_datetime.hour == 8    # 8 AM Monday
    
    # Verify weekend holiday
    assert weekend.type == 'Holiday'
    assert weekend.start_datetime.hour == 17  # 5 PM Friday
    assert weekend.end_datetime.hour == 8     # 8 AM Sunday

def test_consecutive_holidays(config_loader):
    """Test handling of consecutive holidays"""
    holiday_data = [
        {
            "date": "2025-12-24",  # Wednesday
            "name": "Christmas Eve"
        },
        {
            "date": "2025-12-25",  # Thursday
            "name": "Christmas Day"
        }
    ]
    
    assignments = config_loader._create_holiday_assignments(holiday_data)
    
    # Should have two separate holiday assignments
    assert len(assignments) == 2
    
    christmas_eve = next(a for a in assignments if a.name == "Christmas Eve")
    christmas_day = next(a for a in assignments if a.name == "Christmas Day")
    
    # Verify Christmas Eve
    assert christmas_eve.start_datetime.hour == 8  # 8 AM Wednesday
    assert christmas_eve.end_datetime.hour == 8    # 8 AM Thursday
    
    # Verify Christmas Day
    assert christmas_day.start_datetime.hour == 8  # 8 AM Thursday
    assert christmas_day.end_datetime.hour == 8    # 8 AM Friday